"""Alert ingestion: Kafka when enabled, otherwise DB/CSV simulation."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

import structlog

from app.config import Settings, get_settings
from app.core.websocket_manager import manager

logger = structlog.get_logger(__name__)

BroadcastFn = Callable[[dict[str, Any]], Awaitable[None]]


async def broadcast_alert(alert: dict[str, Any]) -> None:
    await manager.broadcast({"event": "alert", "data": alert})


def process_alert(raw: dict[str, Any], *, predict_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> dict[str, Any]:
    alert = {
        "type": str(raw.get("type") or raw.get("Label") or raw.get("label") or "UNKNOWN"),
        "src_ip": raw.get("src_ip") or raw.get("Source IP") or "0.0.0.0",
        "dst_ip": raw.get("dst_ip") or raw.get("Destination IP") or "0.0.0.0",
        "risk_score": float(raw.get("risk_score") or 0.5),
        "timestamp": raw.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "severity": raw.get("severity") or "medium",
        "status": raw.get("status") or "open",
        "raw": {k: v for k, v in raw.items() if k != "raw"},
    }
    if predict_fn:
        prediction = predict_fn(alert)
        alert.update(prediction)
    return alert


class AlertIngestor:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop.clear()
        if self.settings.kafka_enabled:
            self._task = asyncio.create_task(self._kafka_loop(), name="kafka-ingestor")
        else:
            self._task = asyncio.create_task(self._poll_loop(), name="db-ingestor")
        logger.info("ingest.started", kafka=self.settings.kafka_enabled)

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ingest.stopped")

    async def _kafka_loop(self) -> None:
        try:
            from kafka import KafkaConsumer
        except Exception as exc:
            logger.error("kafka.import_failed", error=str(exc))
            await self._poll_loop()
            return
        consumer = KafkaConsumer(
            self.settings.kafka_alert_topic,
            bootstrap_servers=self.settings.kafka_bootstrap_servers.split(","),
            group_id=self.settings.kafka_group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            enable_auto_commit=True,
            auto_offset_reset="latest",
        )
        loop = asyncio.get_running_loop()
        try:
            while not self._stop.is_set():
                records = await loop.run_in_executor(None, lambda: consumer.poll(timeout_ms=500))
                for partition_batch in records.values():
                    for record in partition_batch:
                        alert = process_alert(record.value)
                        await broadcast_alert(alert)
        finally:
            consumer.close()

    async def _poll_loop(self) -> None:
        from sqlalchemy import select

        from app.db.models.alert import Alert
        from app.db.postgres import SessionLocal

        last_id = 0
        while not self._stop.is_set():
            try:
                with SessionLocal() as session:
                    rows = session.scalars(
                        select(Alert).where(Alert.id > last_id).order_by(Alert.id.asc()).limit(25)
                    ).all()
                    for row in rows:
                        last_id = max(last_id, row.id)
                        await broadcast_alert(row.to_dict())
                        await asyncio.sleep(self.settings.alert_stream_interval_seconds)
            except Exception as exc:
                logger.warning("ingest.poll_error", error=str(exc))
            await asyncio.sleep(1.0)


ingestor = AlertIngestor()

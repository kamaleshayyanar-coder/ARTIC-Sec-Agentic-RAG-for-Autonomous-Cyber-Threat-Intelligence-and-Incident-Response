"""WebSocket fan-out for SOC consoles."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
import orjson
import structlog

logger = structlog.get_logger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("ws.connected", clients=len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("ws.disconnected", clients=len(self._connections))

    async def send_personal(self, message: dict[str, Any], websocket: WebSocket) -> None:
        await websocket.send_bytes(orjson.dumps(message))

    async def broadcast(self, message: dict[str, Any]) -> None:
        payload = orjson.dumps(message)
        async with self._lock:
            targets = list(self._connections)
        stale: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_bytes(payload)
            except (WebSocketDisconnect, RuntimeError):
                stale.append(ws)
        for ws in stale:
            await self.disconnect(ws)

    @property
    def client_count(self) -> int:
        return len(self._connections)


manager = WebSocketManager()

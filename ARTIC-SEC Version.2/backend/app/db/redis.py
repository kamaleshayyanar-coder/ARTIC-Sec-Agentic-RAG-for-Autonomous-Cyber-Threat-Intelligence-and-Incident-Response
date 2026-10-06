"""Redis cache and pub/sub."""

from __future__ import annotations

import json
from typing import Any

import redis
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)

_client: redis.Redis | None = None


def connect() -> redis.Redis:
    global _client
    if _client is None:
        settings = get_settings()
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    payload = json.dumps(value, default=str)
    connect().setex(key, ttl, payload)


def cache_get(key: str) -> Any | None:
    raw = connect().get(key)
    if raw is None:
        return None
    return json.loads(raw)


def cache_delete(key: str) -> None:
    connect().delete(key)


def publish(channel: str, message: Any) -> None:
    connect().publish(channel, json.dumps(message, default=str))


def subscribe(channel: str):
    pubsub = connect().pubsub()
    pubsub.subscribe(channel)
    return pubsub


def ping() -> bool:
    return bool(connect().ping())

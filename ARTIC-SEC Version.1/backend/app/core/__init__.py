"""Core package."""

from app.core.websocket_manager import manager
from app.core.kafka_consumer import ingestor

__all__ = ["manager", "ingestor"]

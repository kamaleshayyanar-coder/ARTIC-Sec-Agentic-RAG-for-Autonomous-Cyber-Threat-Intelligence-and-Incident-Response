"""Qdrant client for MITRE / CVE embeddings."""

from __future__ import annotations

from typing import Any, Sequence

import structlog
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from app.config import get_settings

logger = structlog.get_logger(__name__)

_client: QdrantClient | None = None


def connect() -> QdrantClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = QdrantClient(url=settings.qdrant_url, timeout=15)
    return _client


def create_collection(name: str | None = None, vector_size: int | None = None) -> None:
    settings = get_settings()
    collection = name or settings.qdrant_collection
    size = vector_size or settings.embedding_dim
    client = connect()
    existing = [c.name for c in client.get_collections().collections]
    if collection in existing:
        return
    client.create_collection(
        collection_name=collection,
        vectors_config=qm.VectorParams(size=size, distance=qm.Distance.COSINE),
    )
    logger.info("qdrant.collection_created", name=collection, dim=size)


def recreate_collection(name: str | None = None, vector_size: int | None = None) -> None:
    settings = get_settings()
    collection = name or settings.qdrant_collection
    client = connect()
    client.recreate_collection(
        collection_name=collection,
        vectors_config=qm.VectorParams(
            size=vector_size or settings.embedding_dim, distance=qm.Distance.COSINE
        ),
    )


def upsert(points: Sequence[dict[str, Any]], collection: str | None = None) -> None:
    settings = get_settings()
    name = collection or settings.qdrant_collection
    create_collection(name)
    client = connect()
    qpoints = [
        qm.PointStruct(id=p["id"], vector=p["vector"], payload=p.get("payload") or {})
        for p in points
    ]
    client.upsert(collection_name=name, points=qpoints)


def search(query_vector: list[float], limit: int = 5, collection: str | None = None) -> list[dict[str, Any]]:
    settings = get_settings()
    name = collection or settings.qdrant_collection
    client = connect()
    try:
        if hasattr(client, "search"):
            hits = client.search(collection_name=name, query_vector=query_vector, limit=limit, with_payload=True)
        elif hasattr(client, "query_points"):
            res = client.query_points(collection_name=name, query=query_vector, limit=limit, with_payload=True)
            hits = getattr(res, "points", [])
        else:
            hits = []
    except Exception:
        hits = []
    return [
        {
            "id": str(hit.id),
            "score": float(hit.score),
            "payload": hit.payload or {},
        }
        for hit in hits
    ]


def delete(ids: Sequence[str | int], collection: str | None = None) -> None:
    settings = get_settings()
    name = collection or settings.qdrant_collection
    client = connect()
    client.delete(collection_name=name, points_selector=qm.PointIdsList(points=list(ids)))


def ping() -> bool:
    connect().get_collections()
    return True

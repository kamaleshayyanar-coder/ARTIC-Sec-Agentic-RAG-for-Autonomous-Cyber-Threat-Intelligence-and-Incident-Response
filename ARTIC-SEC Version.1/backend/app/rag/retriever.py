"""Hybrid retrieval: dense vectors + BM25 + Neo4j expansion."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from rank_bm25 import BM25Okapi
import structlog

from app.core.security import validate_rag_source
from app.db import neo4j as neo4j_db
from app.db import qdrant as qdrant_db
from app.db import redis as redis_db
from app.rag.embeddings import get_embedding_service

logger = structlog.get_logger(__name__)

_BM25_CORPUS: list[dict[str, Any]] = []
_BM25_MODEL: BM25Okapi | None = None


def register_bm25_corpus(documents: list[dict[str, Any]]) -> None:
    global _BM25_CORPUS, _BM25_MODEL
    _BM25_CORPUS = documents
    tokenized = [str(doc.get("text") or "").lower().split() for doc in documents]
    _BM25_MODEL = BM25Okapi(tokenized) if tokenized else None


def retrieve(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    start = perf_counter()
    cache_key = f"rag:{top_k}:{query}"
    try:
        cached = redis_db.cache_get(cache_key)
        if cached:
            return cached
    except Exception:
        cached = None
    vector = get_embedding_service().embed(query)
    try:
        hits = qdrant_db.search(vector, limit=top_k)
    except Exception as exc:
        logger.warning("retriever.qdrant_failed", error=str(exc))
        hits = []
    results = []
    for hit in hits:
        payload = hit.get("payload") or {}
        source = str(payload.get("source") or "mitre")
        if not validate_rag_source(source):
            continue
        results.append(
            {
                "id": hit["id"],
                "score": hit["score"],
                "text": payload.get("text"),
                "metadata": payload,
                "channel": "vector",
            }
        )
    elapsed_ms = (perf_counter() - start) * 1000
    logger.info("retriever.vector", latency_ms=round(elapsed_ms, 2), k=len(results))
    try:
        redis_db.cache_set(cache_key, results, ttl=60)
    except Exception:
        pass
    return results


def hybrid_search(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    dense = retrieve(query, top_k=top_k * 2)
    sparse: list[dict[str, Any]] = []
    if _BM25_MODEL is not None:
        scores = _BM25_MODEL.get_scores(query.lower().split())
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
        for idx, score in ranked:
            doc = _BM25_CORPUS[idx]
            sparse.append(
                {
                    "id": doc.get("id"),
                    "score": float(score),
                    "text": doc.get("text"),
                    "metadata": doc,
                    "channel": "bm25",
                }
            )
    fused = _rrf(dense, sparse)
    return fused[:top_k]


def graph_search(technique_id: str) -> dict[str, Any]:
    try:
        return neo4j_db.get_technique_details(technique_id)
    except Exception as exc:
        logger.warning("retriever.graph_failed", error=str(exc))
        return {"id": technique_id, "related": []}


def rerank(results: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    q_tokens = set(query.lower().split())
    for item in results:
        text = str(item.get("text") or "").lower()
        overlap = len(q_tokens.intersection(text.split())) / max(1, len(q_tokens))
        item["score"] = float(item.get("score") or 0) + overlap
    return sorted(results, key=lambda x: x.get("score") or 0, reverse=True)


def _rrf(dense: list[dict[str, Any]], sparse: list[dict[str, Any]], k: int = 60) -> list[dict[str, Any]]:
    scores: dict[str, float] = {}
    store: dict[str, dict[str, Any]] = {}
    for rank, item in enumerate(dense):
        key = str(item.get("metadata", {}).get("doc_id") or item.get("id"))
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
        store[key] = item
    for rank, item in enumerate(sparse):
        key = str(item.get("id"))
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
        store.setdefault(key, item)
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    fused = []
    for key, score in ordered:
        item = store[key]
        item = {**item, "score": score, "channel": "hybrid"}
        fused.append(item)
    return fused

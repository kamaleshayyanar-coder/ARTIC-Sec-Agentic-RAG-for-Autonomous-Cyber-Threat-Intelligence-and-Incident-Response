"""Delta indexing into Qdrant + Neo4j."""

from __future__ import annotations

import hashlib
from typing import Any, Iterable

import structlog

from app.config import get_settings
from app.core.security import detect_prompt_injection, validate_rag_source
from app.db import neo4j as neo4j_db
from app.db import qdrant as qdrant_db
from app.rag.embeddings import get_embedding_service

logger = structlog.get_logger(__name__)


def _stable_id(doc_id: str) -> int:
    digest = hashlib.sha1(doc_id.encode("utf-8")).hexdigest()[:16]
    return int(digest, 16) % (2**63 - 1)


def index_document(doc_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
    meta = metadata or {}
    source = str(meta.get("source") or "mitre")
    if detect_prompt_injection(text)["detected"]:
        logger.warning("indexer.rejected_injection", doc_id=doc_id)
        return
    if not validate_rag_source(source):
        logger.warning("indexer.untrusted_source", doc_id=doc_id, source=source)
        return
    vector = get_embedding_service().embed(text)
    payload = {"text": text, "doc_id": doc_id, **meta, "source": source}
    qdrant_db.upsert([{"id": _stable_id(doc_id), "vector": vector, "payload": payload}])
    technique_id = meta.get("technique_id") or doc_id
    if str(technique_id).startswith("T"):
        neo4j_db.add_technique(
            str(technique_id),
            str(meta.get("name") or technique_id),
            text,
            tactic=meta.get("tactic"),
        )


def index_batch(documents: Iterable[dict[str, Any]]) -> int:
    count = 0
    batch: list[dict[str, Any]] = []
    embedder = get_embedding_service()
    texts: list[str] = []
    accepted: list[dict[str, Any]] = []
    for doc in documents:
        text = str(doc.get("text") or doc.get("description") or "")
        source = str(doc.get("source") or "mitre")
        if not text or detect_prompt_injection(text)["detected"] or not validate_rag_source(source):
            continue
        accepted.append(doc)
        texts.append(text)
    if not accepted:
        return 0
    vectors = embedder.embed_batch(texts)
    for doc, vector, text in zip(accepted, vectors, texts, strict=True):
        doc_id = str(doc.get("id") or doc.get("technique_id"))
        payload = {**doc, "text": text, "doc_id": doc_id}
        batch.append({"id": _stable_id(doc_id), "vector": vector, "payload": payload})
        if str(doc.get("technique_id") or doc_id).startswith("T"):
            neo4j_db.add_technique(
                str(doc.get("technique_id") or doc_id),
                str(doc.get("name") or doc_id),
                text,
                tactic=doc.get("tactic"),
            )
        count += 1
        if len(batch) >= 64:
            qdrant_db.upsert(batch)
            batch.clear()
            logger.info("indexer.progress", indexed=count)
    if batch:
        qdrant_db.upsert(batch)
    return count


def delta_index(new_documents: Iterable[dict[str, Any]]) -> int:
    return index_batch(new_documents)


def delete_document(doc_id: str) -> None:
    qdrant_db.delete([_stable_id(doc_id)])


def rebuild_index(documents: Iterable[dict[str, Any]]) -> int:
    settings = get_settings()
    qdrant_db.recreate_collection(settings.qdrant_collection, settings.embedding_dim)
    neo4j_db.create_constraints()
    return index_batch(documents)

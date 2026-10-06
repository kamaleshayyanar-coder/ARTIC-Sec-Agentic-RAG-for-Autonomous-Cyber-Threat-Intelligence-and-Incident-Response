"""SentenceTransformer embeddings with hash fallback for offline/CI."""

from __future__ import annotations

from hashlib import blake2b
from time import perf_counter
from typing import Sequence

import numpy as np
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.dim = settings.embedding_dim
        self._model = None
        self._backend = "hash"

    def load_model(self, model_name: str | None = None) -> "EmbeddingService":
        name = model_name or self.model_name
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(name)
            self.dim = int(self._model.get_sentence_embedding_dimension())
            self._backend = "sentence-transformers"
            logger.info("embeddings.loaded", model=name, dim=self.dim)
        except Exception as exc:
            logger.warning("embeddings.fallback_hash", error=str(exc))
            self._model = None
            self._backend = "hash"
        return self

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        if self._model is None and self._backend != "hash":
            self.load_model()
        if self._model is not None:
            vectors = self._model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
            return [vec.astype(float).tolist() for vec in vectors]
        return [self._hash_embed(text) for text in texts]

    def _hash_embed(self, text: str) -> list[float]:
        digest = blake2b(text.encode("utf-8"), digest_size=64).digest()
        rng = np.random.default_rng(int.from_bytes(digest[:8], "little"))
        vec = rng.normal(size=self.dim)
        norm = np.linalg.norm(vec) or 1.0
        return (vec / norm).astype(float).tolist()

    def benchmark_latency(self, n: int = 50) -> dict[str, float]:
        sample = "Network Service Discovery T1046 port scan against corporate DMZ"
        timings = []
        self.embed(sample)
        for _ in range(n):
            start = perf_counter()
            self.embed(sample)
            timings.append((perf_counter() - start) * 1000)
        arr = np.array(timings)
        return {"p50_ms": float(np.percentile(arr, 50)), "p95_ms": float(np.percentile(arr, 95)), "backend": self._backend}


_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _service
    if _service is None:
        _service = EmbeddingService().load_model()
    return _service

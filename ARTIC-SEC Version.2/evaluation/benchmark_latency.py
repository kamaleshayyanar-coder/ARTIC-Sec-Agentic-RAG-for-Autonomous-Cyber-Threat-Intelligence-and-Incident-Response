"""End-to-end latency: ML + RAG + agent decision path."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import argparse
import asyncio
import statistics
import time
from typing import Any

from app.agents.orchestrator import invoke
from app.ml.classifier import default_classifier
from app.rag.embeddings import get_embedding_service
from app.rag.retriever import hybrid_search


async def once(alert: dict[str, Any]) -> dict[str, float]:
    t0 = time.perf_counter()
    clf = default_classifier()
    t1 = time.perf_counter()
    clf.predict(alert)
    t2 = time.perf_counter()
    get_embedding_service().embed("port scan T1046")
    t3 = time.perf_counter()
    hybrid_search("port scan reconnaissance", top_k=5)
    t4 = time.perf_counter()
    await invoke(alert)
    t5 = time.perf_counter()
    return {
        "ml_ms": (t2 - t1) * 1000,
        "embed_ms": (t3 - t2) * 1000,
        "rag_ms": (t4 - t3) * 1000,
        "agent_ms": (t5 - t4) * 1000,
        "e2e_ms": (t5 - t0) * 1000,
    }


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round((p / 100) * (len(ordered) - 1)))))
    return ordered[idx]


async def run(n: int) -> None:
    alert = {
        "type": "PortScan",
        "src_ip": "203.0.113.10",
        "dst_ip": "10.0.0.5",
        "risk_score": 0.77,
        "severity": "high",
        "ml_prediction": "PortScan",
    }
    samples: list[dict[str, float]] = []
    for _ in range(n):
        samples.append(await once(alert))
    keys = samples[0].keys()
    print(f"{'metric':<12} {'p50':>8} {'p95':>8} {'p99':>8} {'mean':>8}")
    for key in keys:
        series = [s[key] for s in samples]
        print(
            f"{key:<12} {percentile(series, 50):8.1f} {percentile(series, 95):8.1f} "
            f"{percentile(series, 99):8.1f} {statistics.mean(series):8.1f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5)
    args = parser.parse_args()
    asyncio.run(run(args.n))


if __name__ == "__main__":
    main()

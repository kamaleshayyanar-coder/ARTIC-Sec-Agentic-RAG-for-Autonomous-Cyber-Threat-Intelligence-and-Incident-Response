"""Ablation: ML-only, ML+RAG, ML+LLM, full agent stack."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import argparse
import asyncio
import time
from typing import Any

from app.agents.analysis_agent import analyze
from app.agents.orchestrator import invoke
from app.ml.classifier import default_classifier
from app.rag.retriever import hybrid_search


def ml_only(alert: dict[str, Any]) -> dict[str, Any]:
    clf = default_classifier()
    start = time.perf_counter()
    pred = clf.predict(alert)
    return {"variant": "ml_only", "latency_ms": (time.perf_counter() - start) * 1000, "output": pred}


def ml_rag(alert: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    pred = default_classifier().predict(alert)
    docs = hybrid_search(f"{alert.get('type')} {alert.get('src_ip')}", top_k=5)
    return {
        "variant": "ml_rag",
        "latency_ms": (time.perf_counter() - start) * 1000,
        "output": {"pred": pred, "docs": len(docs)},
    }


async def ml_llm(alert: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    pred = default_classifier().predict(alert)
    analysis = await analyze({**alert, **pred}, {})
    return {
        "variant": "ml_llm",
        "latency_ms": (time.perf_counter() - start) * 1000,
        "output": analysis,
    }


async def full(alert: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    result = await invoke(alert)
    return {
        "variant": "full",
        "latency_ms": (time.perf_counter() - start) * 1000,
        "output": {
            "decision": result.get("decision", {}).get("primary_action"),
            "steps": len(result.get("steps") or []),
        },
    }


async def run() -> None:
    alert = {
        "type": "SQLi",
        "src_ip": "198.51.100.23",
        "dst_ip": "10.0.0.8",
        "risk_score": 0.88,
        "severity": "high",
    }
    rows = [ml_only(alert), ml_rag(alert), await ml_llm(alert), await full(alert)]
    print(f"{'variant':<12} {'latency_ms':>12} details")
    for row in rows:
        print(f"{row['variant']:<12} {row['latency_ms']:12.1f} {row['output']}")


def main() -> None:
    argparse.ArgumentParser(description="Component ablation").parse_args()
    asyncio.run(run())


if __name__ == "__main__":
    main()

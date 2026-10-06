"""Threat-intel reconnaissance via hybrid RAG + historical IP lookup."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.alert import Alert
from app.rag.retriever import graph_search, hybrid_search

MITRE_HINTS = {
    "PortScan": "T1046",
    "DDoS": "T1498",
    "DoS": "T1499",
    "SQLi": "T1190",
    "XSS": "T1059",
    "BruteForce": "T1110",
    "Bot": "T1071",
    "Infiltration": "T1021",
    "Heartbleed": "T1190",
    "FTP-Patator": "T1110",
    "SSH-Patator": "T1110.001",
}


def gather_intel(alert: dict[str, Any], db: Session | None = None) -> dict[str, Any]:
    query = (
        f"{alert.get('type')} {alert.get('ml_prediction') or ''} "
        f"source {alert.get('src_ip')} destination {alert.get('dst_ip')} MITRE ATT&CK"
    )
    docs = hybrid_search(query, top_k=5)
    technique = alert.get("mitre_technique") or MITRE_HINTS.get(str(alert.get("type")), "T1046")
    graph = graph_search(technique)
    history: list[dict[str, Any]] = []
    if db is not None and alert.get("src_ip"):
        rows = db.scalars(
            select(Alert).where(Alert.src_ip == alert["src_ip"]).order_by(Alert.timestamp.desc()).limit(10)
        ).all()
        history = [row.to_dict() for row in rows]
    return {
        "technique_id": technique,
        "documents": docs,
        "graph": graph,
        "source_history": history,
        "attack_stage": _stage(technique),
    }


def enrich_alert(alert: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(alert)
    enriched["mitre_technique"] = context.get("technique_id") or alert.get("mitre_technique")
    enriched["attack_stage"] = context.get("attack_stage")
    docs = context.get("documents") or []
    enriched["intel_confidence"] = min(0.99, 0.45 + 0.1 * len(docs))
    enriched["citations"] = [
        {
            "id": doc.get("id"),
            "text": str(doc.get("text") or "")[:400],
            "score": doc.get("score"),
        }
        for doc in docs[:3]
    ]
    return enriched


def _stage(technique_id: str) -> str:
    mapping = {
        "T1046": "reconnaissance",
        "T1595": "reconnaissance",
        "T1190": "initial_access",
        "T1110": "credential_access",
        "T1021": "lateral_movement",
        "T1498": "impact",
        "T1499": "impact",
        "T1071": "command_and_control",
    }
    prefix = technique_id.split(".")[0]
    return mapping.get(prefix, "unknown")

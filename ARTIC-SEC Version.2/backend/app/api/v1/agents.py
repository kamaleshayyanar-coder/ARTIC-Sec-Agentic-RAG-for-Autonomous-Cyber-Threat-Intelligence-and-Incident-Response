"""Agent health and audit endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.agents.guardrail_agent import latest_audit
from app.core.websocket_manager import manager

router = APIRouter()

_AGENT_META = [
    {"id": "recon", "name": "Recon Agent", "description": "MITRE / CVE / historical IP intel"},
    {"id": "analysis", "name": "Analysis Agent", "description": "LLM root-cause and TTP mapping"},
    {"id": "response", "name": "Response Agent", "description": "Containment policy engine"},
    {"id": "report", "name": "Report Agent", "description": "NIST SP 800-61 reporting"},
    {"id": "guardrail", "name": "Guardrail Agent", "description": "Injection, allow-list, rate limits"},
]


@router.get("/status")
def agent_status() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    agents = []
    for meta in _AGENT_META:
        agents.append(
            {
                **meta,
                "status": "active",
                "last_run": now,
                "current_task": "idle",
            }
        )
    return {"agents": agents, "websocket_clients": manager.client_count, "ts": now}


@router.get("/audit")
def audit(limit: int = 100) -> dict:
    return {"items": latest_audit(limit)}

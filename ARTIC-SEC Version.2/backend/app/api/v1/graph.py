"""Attack graph endpoints backed by Neo4j with safe fallbacks."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.db import neo4j as neo4j_db
from app.db.models.incident import Incident
from app.rag.knowledge_graph import get_attack_graph, get_technique_details
from app.schemas.response import GraphPayload

router = APIRouter()


@router.get("", response_model=GraphPayload)
def graph() -> GraphPayload:
    try:
        payload = get_attack_graph()
    except Exception:
        payload = neo4j_db._fallback_graph()
    return GraphPayload(**payload)


@router.get("/incident/{incident_id}", response_model=GraphPayload)
def incident_graph(incident_id: int, db: DbSession) -> GraphPayload:
    if db.get(Incident, incident_id) is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    try:
        payload = get_attack_graph(incident_id)
    except Exception:
        payload = neo4j_db._fallback_graph()
    return GraphPayload(**payload)


@router.get("/mitre-technique/{technique_id}")
def technique(technique_id: str) -> dict:
    try:
        return get_technique_details(technique_id)
    except Exception:
        return {"id": technique_id, "name": technique_id, "description": "", "tactics": [], "related": []}

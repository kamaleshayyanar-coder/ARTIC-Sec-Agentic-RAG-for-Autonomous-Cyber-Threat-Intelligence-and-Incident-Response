"""Incident records and reasoning traces."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func

from app.agents.orchestrator import invoke
from app.api.deps import CurrentUser, DbSession
from app.db.models.alert import Alert
from app.db.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentResponse, IncidentUpdate
from app.schemas.response import PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[IncidentResponse])
def list_incidents(
    db: DbSession,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, alias="status"),
) -> PaginatedResponse[IncidentResponse]:
    stmt = select(Incident)
    count_stmt = select(func.count(Incident.id))
    if status_filter:
        stmt = stmt.where(Incident.status == status_filter)
        count_stmt = count_stmt.where(Incident.status == status_filter)
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(stmt.order_by(Incident.created_at.desc()).offset(offset).limit(limit)).all()
    return PaginatedResponse(
        items=[IncidentResponse.model_validate(r) for r in rows],
        total=total,
        page=(offset // limit) + 1,
        page_size=limit,
        offset=offset,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: DbSession) -> IncidentResponse:
    row = db.get(Incident, incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentResponse.model_validate(row)


@router.post("", response_model=IncidentResponse, status_code=201)
def create_incident(payload: IncidentCreate, db: DbSession) -> IncidentResponse:
    row = Incident(
        title=payload.title,
        severity=payload.severity,
        mitre_techniques=json.dumps(payload.mitre_techniques or []),
        status="open",
    )
    db.add(row)
    db.flush()
    if payload.alert_ids:
        alerts = db.scalars(select(Alert).where(Alert.id.in_(payload.alert_ids))).all()
        for alert in alerts:
            alert.incident_id = row.id
    db.commit()
    db.refresh(row)
    return IncidentResponse.model_validate(row)


@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(incident_id: int, payload: IncidentUpdate, db: DbSession, _: CurrentUser) -> IncidentResponse:
    row = db.get(Incident, incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("status") == "resolved" and row.resolved_at is None:
        row.resolved_at = datetime.now(timezone.utc)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return IncidentResponse.model_validate(row)


@router.get("/{incident_id}/reasoning")
def reasoning(incident_id: int, db: DbSession) -> dict:
    row = db.get(Incident, incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if row.reasoning_json:
        return json.loads(row.reasoning_json)
    return {"steps": [], "message": "No agent trace stored yet"}


@router.post("/{incident_id}/run-agents")
async def run_agents(incident_id: int, db: DbSession) -> dict:
    row = db.get(Incident, incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    alert = row.alerts[0].to_dict() if row.alerts else {"type": "UNKNOWN", "src_ip": "0.0.0.0", "dst_ip": "0.0.0.0", "risk_score": 0.5}
    result = await invoke(alert, db=db)
    report = result.get("report") or {}
    row.agent_report = (report.get("markdown") if isinstance(report, dict) else str(report)) or row.agent_report
    row.reasoning_json = json.dumps(result.get("steps") or [], default=str)
    techniques = (result.get("analysis") or {}).get("ttps")
    if techniques:
        row.mitre_techniques = json.dumps(techniques)
    db.commit()
    return {"incident_id": incident_id, "steps": result.get("steps"), "report": report}

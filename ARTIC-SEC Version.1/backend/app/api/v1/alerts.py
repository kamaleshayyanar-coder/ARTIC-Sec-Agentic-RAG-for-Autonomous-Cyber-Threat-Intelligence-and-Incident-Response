"""Alert CRUD, geo markers, and agent enrichment."""

from __future__ import annotations

from hashlib import sha256
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func

from app.agents.orchestrator import invoke
from fastapi import Depends

from app.api.deps import CurrentUser, DbSession, require_admin
from app.db.models.alert import Alert
from app.ml import default_classifier, default_detector
from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate, GeoAlert
from app.schemas.response import APIResponse, PaginatedResponse

router = APIRouter()
_classifier = None
_detector = None


def _ml():
    global _classifier, _detector
    if _classifier is None:
        _classifier = default_classifier()
        _detector = default_detector()
    return _classifier, _detector


def _ip_coords(ip: str) -> tuple[float, float]:
    digest = sha256(ip.encode()).digest()
    lat = (int.from_bytes(digest[:4], "big") / 2**32) * 140 - 70
    lon = (int.from_bytes(digest[4:8], "big") / 2**32) * 360 - 180
    return round(lat, 4), round(lon, 4)


@router.get("", response_model=PaginatedResponse[AlertResponse])
def list_alerts(
    db: DbSession,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    attack_type: Optional[str] = Query(None, alias="type"),
) -> PaginatedResponse[AlertResponse]:
    stmt = select(Alert)
    count_stmt = select(func.count(Alert.id))
    if severity:
        stmt = stmt.where(Alert.severity == severity)
        count_stmt = count_stmt.where(Alert.severity == severity)
    if status_filter:
        stmt = stmt.where(Alert.status == status_filter)
        count_stmt = count_stmt.where(Alert.status == status_filter)
    if attack_type:
        stmt = stmt.where(Alert.type == attack_type)
        count_stmt = count_stmt.where(Alert.type == attack_type)
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(stmt.order_by(Alert.timestamp.desc()).offset(offset).limit(limit)).all()
    page = (offset // limit) + 1
    return PaginatedResponse(
        items=[AlertResponse.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=limit,
        offset=offset,
    )


@router.get("/geo", response_model=list[GeoAlert])
def geo_alerts(db: DbSession, limit: int = Query(200, ge=1, le=1000)) -> list[GeoAlert]:
    rows = db.scalars(select(Alert).order_by(Alert.timestamp.desc()).limit(limit)).all()
    out: list[GeoAlert] = []
    for row in rows:
        lat, lon = _ip_coords(row.src_ip)
        out.append(
            GeoAlert(
                id=row.id,
                type=row.type,
                src_ip=row.src_ip,
                severity=row.severity,
                lat=lat,
                lon=lon,
                risk_score=row.risk_score,
            )
        )
    return out


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: DbSession) -> AlertResponse:
    row = db.get(Alert, alert_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse.model_validate(row)


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(payload: AlertCreate, db: DbSession) -> AlertResponse:
    clf, det = _ml()
    prediction = clf.predict(payload.model_dump())
    anomaly = det.predict(payload.model_dump())
    row = Alert(
        **payload.model_dump(),
        ml_prediction=prediction.get("ml_prediction"),
    )
    if not row.mitre_technique:
        from app.agents.recon_agent import MITRE_HINTS

        row.mitre_technique = MITRE_HINTS.get(row.type)
    row.risk_score = max(row.risk_score, anomaly)
    db.add(row)
    db.commit()
    db.refresh(row)
    return AlertResponse.model_validate(row)


@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert(alert_id: int, payload: AlertUpdate, db: DbSession, _: CurrentUser) -> AlertResponse:
    row = db.get(Alert, alert_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return AlertResponse.model_validate(row)


@router.delete("/{alert_id}", response_model=APIResponse)
def delete_alert(alert_id: int, db: DbSession, _: object = Depends(require_admin)) -> APIResponse:
    row = db.get(Alert, alert_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(row)
    db.commit()
    return APIResponse(success=True, message=f"deleted {alert_id}")


@router.post("/{alert_id}/investigate")
async def investigate_alert(alert_id: int, db: DbSession) -> dict:
    row = db.get(Alert, alert_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    result = await invoke(row.to_dict(), db=db)
    return {
        "alert": result.get("alert"),
        "analysis": result.get("analysis"),
        "decision": result.get("decision"),
        "guardrail": result.get("guardrail"),
        "report": result.get("report"),
        "steps": result.get("steps"),
    }

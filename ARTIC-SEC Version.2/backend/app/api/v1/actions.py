"""SOAR playbook actions: propose -> (auto-execute | pending_approval) -> approve/reject -> executed.

Ties together response_agent.decide_response (what to do), core.security
guardrail_check (is it allowed / does it need a human), and
playbook_executor (actually "do" it, simulated). Every transition is
audit-logged via core.security.audit_log_action.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.agents import playbook_executor
from app.agents.analysis_agent import analyze
from app.agents.response_agent import decide_response
from app.api.deps import CurrentUser, DbSession, require_role
from app.core.security import audit_log_action, guardrail_check
from app.config import get_settings
from app.db.models.action import PlaybookAction
from app.db.models.alert import Alert
from app.schemas.action import ActionDecision, ActionOut

router = APIRouter()


def _actor(user: CurrentUser) -> str:
    return user.username if user is not None else "anonymous"


@router.post("/propose/{alert_id}", response_model=ActionOut, status_code=status.HTTP_201_CREATED)
async def propose_action(alert_id: int, db: DbSession, current: CurrentUser) -> ActionOut:
    """Run the response agent + guardrails on an alert and persist the
    resulting playbook action, auto-executing it if it's low-risk and
    AUTO_EXECUTE_LOW_RISK is on, otherwise queuing it for human approval."""
    settings = get_settings()
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alert not found")

    analysis = await analyze(alert.to_dict(), {})
    decision = decide_response(alert.to_dict(), analysis)
    guardrail = guardrail_check(decision, agent_id="response")

    row = PlaybookAction(
        alert_id=alert.id,
        action_type=decision["primary_action"],
        target=decision["target"] or alert.src_ip,
        severity=decision["severity"],
        risk_score=decision["risk_score"],
        justification=decision.get("justification"),
        guardrail_json=json.dumps({"allowed": guardrail.allowed, "reasons": guardrail.reasons}),
        created_by=_actor(current),
        status="pending_approval",
    )

    can_auto_execute = guardrail.allowed and not decision["requires_approval"] and settings.auto_execute_low_risk
    if can_auto_execute:
        result = playbook_executor.run_and_audit(
            row.action_type, row.target, agent_id="response", extra={"alert_id": alert.id, "auto": True}
        )
        row.status = "auto_executed" if result.get("status") == "executed" else "failed"
        row.result_json = json.dumps(result)
        row.executed_at = datetime.now(timezone.utc)
    else:
        audit_log_action(decision, {"allowed": guardrail.allowed, "reasons": guardrail.reasons, "queued": True}, agent_id="response")

    db.add(row)
    db.commit()
    db.refresh(row)
    return ActionOut(**row.to_dict())


@router.get("", response_model=list[ActionOut])
def list_actions(
    db: DbSession,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
) -> list[ActionOut]:
    stmt = select(PlaybookAction).order_by(PlaybookAction.created_at.desc()).limit(limit)
    if status_filter:
        stmt = stmt.where(PlaybookAction.status == status_filter)
    rows = db.scalars(stmt).all()
    return [ActionOut(**row.to_dict()) for row in rows]


@router.get("/{action_id}", response_model=ActionOut)
def get_action(action_id: int, db: DbSession) -> ActionOut:
    row = db.get(PlaybookAction, action_id)
    if row is None:
        raise HTTPException(status_code=404, detail="action not found")
    return ActionOut(**row.to_dict())


@router.post("/{action_id}/approve", response_model=ActionOut)
def approve_action(
    action_id: int,
    payload: ActionDecision,
    db: DbSession,
    current: CurrentUser,
    _: object = Depends(require_role("approver", "admin")),
) -> ActionOut:
    row = db.get(PlaybookAction, action_id)
    if row is None:
        raise HTTPException(status_code=404, detail="action not found")
    if row.status not in {"pending_approval", "failed"}:
        raise HTTPException(status_code=409, detail=f"action already in terminal state: {row.status}")

    # Re-check guardrails with human_approved=True so the internal-IP /
    # destructive-action gate that originally queued this can now pass.
    guardrail = guardrail_check({"type": row.action_type, "target": row.target, "human_approved": True}, agent_id="approver")
    if not guardrail.allowed:
        row.status = "rejected"
        row.decided_by = _actor(current)
        row.decided_at = datetime.now(timezone.utc)
        row.result_json = json.dumps({"status": "rejected", "reasons": guardrail.reasons})
        db.commit()
        db.refresh(row)
        raise HTTPException(status_code=422, detail=f"guardrail still blocks this action: {guardrail.reasons}")

    result = playbook_executor.run_and_audit(
        row.action_type, row.target, agent_id="approver", extra={"alert_id": row.alert_id, "approved_by": _actor(current), "note": payload.note}
    )
    row.status = "executed" if result.get("status") == "executed" else "failed"
    row.decided_by = _actor(current)
    row.decided_at = datetime.now(timezone.utc)
    row.executed_at = datetime.now(timezone.utc)
    row.result_json = json.dumps(result)
    db.commit()
    db.refresh(row)
    return ActionOut(**row.to_dict())


@router.post("/{action_id}/reject", response_model=ActionOut)
def reject_action(
    action_id: int,
    payload: ActionDecision,
    db: DbSession,
    current: CurrentUser,
    _: object = Depends(require_role("approver", "admin")),
) -> ActionOut:
    row = db.get(PlaybookAction, action_id)
    if row is None:
        raise HTTPException(status_code=404, detail="action not found")
    if row.status not in {"pending_approval", "failed"}:
        raise HTTPException(status_code=409, detail=f"action already in terminal state: {row.status}")
    row.status = "rejected"
    row.decided_by = _actor(current)
    row.decided_at = datetime.now(timezone.utc)
    row.result_json = json.dumps({"status": "rejected", "note": payload.note})
    db.commit()
    db.refresh(row)
    audit_log_action(
        {"type": row.action_type, "target": row.target}, {"status": "rejected", "by": _actor(current)}, agent_id="approver"
    )
    return ActionOut(**row.to_dict())

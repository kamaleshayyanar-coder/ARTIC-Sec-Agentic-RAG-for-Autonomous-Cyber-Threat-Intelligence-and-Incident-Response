from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ActionOut(BaseModel):
    id: int
    alert_id: Optional[int] = None
    action_type: str
    target: str
    severity: str
    risk_score: float
    status: str
    justification: Optional[str] = None
    created_by: str
    decided_by: Optional[str] = None
    created_at: Optional[str] = None
    decided_at: Optional[str] = None
    executed_at: Optional[str] = None


class ActionDecision(BaseModel):
    note: Optional[str] = None

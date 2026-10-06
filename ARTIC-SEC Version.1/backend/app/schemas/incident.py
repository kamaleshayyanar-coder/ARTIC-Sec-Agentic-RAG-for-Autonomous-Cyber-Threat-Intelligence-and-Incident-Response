from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.alert import AlertResponse, Severity

IncidentStatus = Literal["open", "investigating", "contained", "resolved"]


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    severity: Severity = "medium"
    mitre_techniques: Optional[list[str]] = None
    alert_ids: list[int] = Field(default_factory=list)


class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    severity: Optional[Severity] = None
    assigned_to: Optional[str] = None
    agent_report: Optional[str] = None


class IncidentResponse(BaseModel):
    id: int
    title: str
    status: str
    severity: str
    mitre_techniques: Optional[str] = None
    agent_report: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    alerts: list[AlertResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}

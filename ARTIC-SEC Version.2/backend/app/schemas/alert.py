from datetime import datetime
from ipaddress import IPv4Address
from typing import Literal, Optional

from pydantic import BaseModel, Field, IPvAnyAddress, field_validator

Severity = Literal["low", "medium", "high", "critical"]
AlertStatus = Literal["open", "investigating", "resolved", "false_positive"]


class AlertCreate(BaseModel):
    type: str = Field(..., min_length=1, max_length=64)
    src_ip: str
    dst_ip: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    ml_prediction: Optional[str] = None
    mitre_technique: Optional[str] = Field(default=None, max_length=32)
    severity: Severity = "medium"
    status: AlertStatus = "open"
    incident_id: Optional[int] = None

    @field_validator("src_ip", "dst_ip")
    @classmethod
    def valid_ipv4(cls, value: str) -> str:
        IPv4Address(value)
        return value


class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    severity: Optional[Severity] = None
    incident_id: Optional[int] = None
    mitre_technique: Optional[str] = None


class AlertResponse(BaseModel):
    id: int
    type: str
    src_ip: str
    dst_ip: str
    risk_score: float
    ml_prediction: Optional[str] = None
    mitre_technique: Optional[str] = None
    severity: str
    status: str
    timestamp: Optional[datetime] = None
    incident_id: Optional[int] = None
    analysis: Optional[dict] = None

    model_config = {"from_attributes": True}


class GeoAlert(BaseModel):
    id: int
    type: str
    src_ip: str
    severity: str
    lat: float
    lon: float
    risk_score: float

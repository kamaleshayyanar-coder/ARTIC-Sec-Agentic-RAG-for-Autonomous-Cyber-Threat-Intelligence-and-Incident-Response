from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: str = "ok"


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 50
    offset: int = 0


class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int


class MetricsResponse(BaseModel):
    total_alerts: int
    high_risk_count: int
    mttd_seconds: float
    mttr_seconds: float
    auto_resolution_rate: float
    open_incidents: int
    websocket_clients: int


class HourlyPoint(BaseModel):
    hour: str
    count: int
    high_risk: int = 0


class AttackTypeCount(BaseModel):
    type: str
    count: int


class GraphPayload(BaseModel):
    nodes: list[dict]
    links: list[dict]


class InsightQuery(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    alert_id: Optional[int] = None

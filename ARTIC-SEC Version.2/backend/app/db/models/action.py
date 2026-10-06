from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base

# pending_approval -> approved -> executed
#                  -> rejected
# auto_executed is the low-risk fast path (see AUTO_EXECUTE_LOW_RISK)
ACTION_STATUSES = (
    "pending_approval",
    "approved",
    "rejected",
    "executed",
    "auto_executed",
    "failed",
)


class PlaybookAction(Base):
    __tablename__ = "playbook_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[Optional[int]] = mapped_column(ForeignKey("alerts.id"), nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(32), index=True)
    target: Mapped[str] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="pending_approval", index=True)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    guardrail_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(64), default="system")
    decided_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "action_type": self.action_type,
            "target": self.target,
            "severity": self.severity,
            "risk_score": self.risk_score,
            "status": self.status,
            "justification": self.justification,
            "created_by": self.created_by,
            "decided_by": self.decided_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }

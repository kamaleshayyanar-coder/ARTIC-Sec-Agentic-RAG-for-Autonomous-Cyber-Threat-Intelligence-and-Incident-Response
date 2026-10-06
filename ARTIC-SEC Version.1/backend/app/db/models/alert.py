from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(64), index=True)
    src_ip: Mapped[str] = mapped_column(String(64), index=True)
    dst_ip: Mapped[str] = mapped_column(String(64), index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    ml_prediction: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mitre_technique: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    severity: Mapped[str] = mapped_column(String(16), default="medium", index=True)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    incident_id: Mapped[Optional[int]] = mapped_column(ForeignKey("incidents.id"), nullable=True)
    payload_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incident: Mapped[Optional["Incident"]] = relationship(back_populates="alerts")  # noqa: F821

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "risk_score": self.risk_score,
            "ml_prediction": self.ml_prediction,
            "mitre_technique": self.mitre_technique,
            "severity": self.severity,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "incident_id": self.incident_id,
        }

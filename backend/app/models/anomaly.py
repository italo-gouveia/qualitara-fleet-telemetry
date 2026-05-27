from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("vehicle_states.vehicle_id"), nullable=False
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    detail: Mapped[Any] = mapped_column(JSON, nullable=False)
    telemetry_event_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("telemetry_events.id"), nullable=True
    )

    __table_args__ = (
        Index("ix_anomalies_vehicle_detected_at", "vehicle_id", "detected_at"),
    )

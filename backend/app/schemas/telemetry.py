from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field


class VehicleStatus(StrEnum):
    IDLE = "idle"
    MOVING = "moving"
    CHARGING = "charging"
    FAULT = "fault"


class TelemetryEventIn(BaseModel):
    vehicle_id: Annotated[str, Field(min_length=1, max_length=20)]
    timestamp: datetime
    lat: float
    lon: float
    battery_pct: Annotated[int, Field(ge=0, le=100)]
    speed_mps: Annotated[float, Field(ge=0)]
    status: VehicleStatus
    error_codes: list[str] = []
    zone_entered: str | None = None


class IngestResult(BaseModel):
    id: int
    anomalies_detected: int

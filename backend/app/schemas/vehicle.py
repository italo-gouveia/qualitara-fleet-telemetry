from datetime import datetime

from pydantic import BaseModel

from app.schemas.telemetry import VehicleStatus


class StatusUpdateRequest(BaseModel):
    status: VehicleStatus


class StatusUpdateResponse(BaseModel):
    vehicle_id: str
    status: str
    mission_cancelled: bool
    maintenance_record_id: int | None = None


class MissionResponse(BaseModel):
    id: int
    vehicle_id: str
    status: str
    created_at: datetime
    cancelled_at: datetime | None = None


class MaintenanceRecordResponse(BaseModel):
    id: int
    vehicle_id: str
    mission_id: int
    reason: str
    created_at: datetime

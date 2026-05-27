from pydantic import BaseModel

from app.schemas.telemetry import VehicleStatus


class StatusUpdateRequest(BaseModel):
    status: VehicleStatus


class StatusUpdateResponse(BaseModel):
    vehicle_id: str
    status: str
    mission_cancelled: bool
    maintenance_record_id: int | None = None

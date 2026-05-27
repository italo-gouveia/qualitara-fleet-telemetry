from datetime import datetime

from pydantic import BaseModel


class FleetStateResponse(BaseModel):
    idle: int = 0
    moving: int = 0
    charging: int = 0
    fault: int = 0
    total: int = 0


class VehicleStateResponse(BaseModel):
    vehicle_id: str
    status: str
    battery_pct: int
    lat: float
    lon: float
    updated_at: datetime

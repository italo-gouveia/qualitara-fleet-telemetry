from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AnomalyResponse(BaseModel):
    id: int
    vehicle_id: str
    detected_at: datetime
    type: str
    detail: Any

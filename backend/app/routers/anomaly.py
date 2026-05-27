from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.anomaly_repository import get_anomalies
from app.schemas.anomaly import AnomalyResponse

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[AnomalyResponse])
async def list_anomalies(
    vehicle_id: Annotated[str | None, Query()] = None,
    start: Annotated[datetime | None, Query()] = None,
    end: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    session: AsyncSession = Depends(get_session),
) -> list[AnomalyResponse]:
    rows = await get_anomalies(session, vehicle_id=vehicle_id, start=start, end=end, limit=limit)
    return [
        AnomalyResponse(
            id=row.id,
            vehicle_id=row.vehicle_id,
            detected_at=row.detected_at,
            type=row.type,
            detail=row.detail,
        )
        for row in rows
    ]

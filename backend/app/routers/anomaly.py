from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.anomaly import AnomalyResponse
from app.services.anomaly import query_anomalies

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[AnomalyResponse])
async def list_anomalies(
    vehicle_id: Annotated[str | None, Query()] = None,
    start: Annotated[datetime | None, Query()] = None,
    end: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    session: AsyncSession = Depends(get_session),
) -> list[AnomalyResponse]:
    return await query_anomalies(
        session, vehicle_id=vehicle_id, start=start, end=end, limit=limit
    )

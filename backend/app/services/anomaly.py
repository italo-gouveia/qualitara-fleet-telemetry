from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.anomaly_repository import get_anomalies
from app.schemas.anomaly import AnomalyResponse


async def query_anomalies(
    session: AsyncSession,
    vehicle_id: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
) -> list[AnomalyResponse]:
    """Return anomalies with optional filters applied."""
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

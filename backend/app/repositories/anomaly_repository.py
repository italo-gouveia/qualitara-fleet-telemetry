from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anomaly import Anomaly

_MAX_LIMIT = 500


async def get_anomalies(
    session: AsyncSession,
    vehicle_id: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
) -> list[Anomaly]:
    capped = min(limit, _MAX_LIMIT)
    query = select(Anomaly).order_by(Anomaly.detected_at.desc()).limit(capped)
    if vehicle_id:
        query = query.where(Anomaly.vehicle_id == vehicle_id)
    if start:
        query = query.where(Anomaly.detected_at >= start)
    if end:
        query = query.where(Anomaly.detected_at <= end)
    result = await session.execute(query)
    return list(result.scalars().all())

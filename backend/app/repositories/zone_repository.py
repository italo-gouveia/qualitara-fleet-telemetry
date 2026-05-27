from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.zone import ZoneCount


async def get_all_zone_counts(session: AsyncSession) -> dict[str, int]:
    rows = await session.execute(select(ZoneCount).order_by(ZoneCount.zone_id))
    return {row.zone_id: row.entry_count for row in rows.scalars()}

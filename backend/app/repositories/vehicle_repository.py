from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import VehicleState
from app.schemas.fleet import FleetStateResponse, VehicleStateResponse

_ALL_STATUSES = ("idle", "moving", "charging", "fault")


async def get_fleet_aggregate(session: AsyncSession) -> FleetStateResponse:
    rows = await session.execute(
        select(VehicleState.status, func.count().label("count")).group_by(
            VehicleState.status
        )
    )
    counts = {status: 0 for status in _ALL_STATUSES}
    for status, count in rows:
        counts[status] = count

    return FleetStateResponse(
        idle=counts["idle"],
        moving=counts["moving"],
        charging=counts["charging"],
        fault=counts["fault"],
        total=sum(counts.values()),
    )


async def get_all_vehicle_states(
    session: AsyncSession, limit: int = 50, offset: int = 0
) -> list[VehicleStateResponse]:
    rows = await session.execute(
        select(VehicleState).order_by(VehicleState.vehicle_id).limit(limit).offset(offset)
    )
    return [
        VehicleStateResponse(
            vehicle_id=vs.vehicle_id,
            status=vs.status,
            battery_pct=vs.battery_pct,
            lat=vs.lat,
            lon=vs.lon,
            updated_at=vs.updated_at,
        )
        for vs in rows.scalars()
    ]

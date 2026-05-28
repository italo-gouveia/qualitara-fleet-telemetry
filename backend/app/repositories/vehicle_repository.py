from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import MaintenanceRecord, Mission, VehicleState
from app.schemas.fleet import FleetStateResponse, VehicleStateResponse
from app.schemas.vehicle import MaintenanceRecordResponse, MissionResponse

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


async def get_missions_by_vehicle(
    vehicle_id: str, session: AsyncSession, limit: int = 50, offset: int = 0
) -> list[MissionResponse]:
    rows = await session.execute(
        select(Mission)
        .where(Mission.vehicle_id == vehicle_id)
        .order_by(Mission.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        MissionResponse(
            id=m.id,
            vehicle_id=m.vehicle_id,
            status=m.status,
            created_at=m.created_at,
            cancelled_at=m.cancelled_at,
        )
        for m in rows.scalars()
    ]


async def get_maintenance_by_vehicle(
    vehicle_id: str, session: AsyncSession, limit: int = 50, offset: int = 0
) -> list[MaintenanceRecordResponse]:
    rows = await session.execute(
        select(MaintenanceRecord)
        .where(MaintenanceRecord.vehicle_id == vehicle_id)
        .order_by(MaintenanceRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        MaintenanceRecordResponse(
            id=r.id,
            vehicle_id=r.vehicle_id,
            mission_id=r.mission_id,
            reason=r.reason,
            created_at=r.created_at,
        )
        for r in rows.scalars()
    ]


async def get_vehicle_by_id(
    vehicle_id: str, session: AsyncSession
) -> VehicleStateResponse | None:
    row = await session.execute(
        select(VehicleState).where(VehicleState.vehicle_id == vehicle_id)
    )
    vs = row.scalar_one_or_none()
    if vs is None:
        return None
    return VehicleStateResponse(
        vehicle_id=vs.vehicle_id,
        status=vs.status,
        battery_pct=vs.battery_pct,
        lat=vs.lat,
        lon=vs.lon,
        updated_at=vs.updated_at,
    )

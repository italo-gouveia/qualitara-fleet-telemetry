from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.vehicle_repository import get_all_vehicle_states, get_fleet_aggregate
from app.repositories.zone_repository import get_all_zone_counts
from app.schemas.fleet import FleetStateResponse, VehicleStateResponse


async def get_fleet_state(session: AsyncSession) -> FleetStateResponse:
    """Return per-status vehicle counts."""
    return await get_fleet_aggregate(session)


async def get_vehicles(
    session: AsyncSession, limit: int = 50, offset: int = 0
) -> list[VehicleStateResponse]:
    """Return known vehicles ordered by vehicle_id, with pagination."""
    return await get_all_vehicle_states(session, limit=limit, offset=offset)


async def get_zone_counts(session: AsyncSession) -> dict[str, int]:
    """Return entry counts for all 20 zones."""
    return await get_all_zone_counts(session)

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.vehicle_repository import get_all_vehicle_states, get_fleet_aggregate
from app.repositories.zone_repository import get_all_zone_counts
from app.schemas.fleet import FleetStateResponse, VehicleStateResponse

router = APIRouter(tags=["fleet"])


@router.get("/fleet/state", response_model=FleetStateResponse)
async def fleet_state(session: AsyncSession = Depends(get_session)) -> FleetStateResponse:
    return await get_fleet_aggregate(session)


@router.get("/zones/counts", response_model=dict[str, int])
async def zone_counts(session: AsyncSession = Depends(get_session)) -> dict[str, int]:
    return await get_all_zone_counts(session)


@router.get("/vehicles", response_model=list[VehicleStateResponse])
async def vehicles(
    session: AsyncSession = Depends(get_session),
) -> list[VehicleStateResponse]:
    return await get_all_vehicle_states(session)

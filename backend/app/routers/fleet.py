from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.fleet import FleetStateResponse, VehicleStateResponse
from app.services.fleet import get_fleet_state, get_vehicles, get_zone_counts

router = APIRouter(tags=["fleet"])


@router.get("/fleet/state", response_model=FleetStateResponse)
async def fleet_state(session: AsyncSession = Depends(get_session)) -> FleetStateResponse:
    return await get_fleet_state(session)


@router.get("/zones/counts", response_model=dict[str, int])
async def zone_counts(session: AsyncSession = Depends(get_session)) -> dict[str, int]:
    return await get_zone_counts(session)


@router.get("/vehicles", response_model=list[VehicleStateResponse])
async def vehicles(session: AsyncSession = Depends(get_session)) -> list[VehicleStateResponse]:
    return await get_vehicles(session)

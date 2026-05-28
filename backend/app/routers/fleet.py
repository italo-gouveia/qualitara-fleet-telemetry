from typing import Annotated

from fastapi import APIRouter, Query

from app.database import SessionDep
from app.schemas.fleet import FleetStateResponse, VehicleStateResponse
from app.services.fleet import get_fleet_state, get_vehicles, get_zone_counts

router = APIRouter(tags=["fleet"])


@router.get("/fleet/state", response_model=FleetStateResponse, summary="Per-status vehicle counts")
async def fleet_state(session: SessionDep) -> FleetStateResponse:
    return await get_fleet_state(session)


@router.get("/zones/counts", response_model=dict[str, int], summary="Entry counts for all 20 zones")
async def zone_counts(session: SessionDep) -> dict[str, int]:
    return await get_zone_counts(session)


@router.get(
    "/vehicles",
    response_model=list[VehicleStateResponse],
    summary="All known vehicles, paginated",
)
async def vehicles(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100, description="Max vehicles to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of vehicles to skip")] = 0,
) -> list[VehicleStateResponse]:
    return await get_vehicles(session, limit=limit, offset=offset)

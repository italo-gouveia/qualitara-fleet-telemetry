from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.database import SessionDep
from app.schemas.fleet import VehicleStateResponse
from app.schemas.vehicle import (
    MaintenanceRecordResponse,
    MissionResponse,
    StatusUpdateRequest,
    StatusUpdateResponse,
)
from app.services.vehicle import (
    VehicleNotFound,
    get_vehicle,
    get_vehicle_maintenance,
    get_vehicle_missions,
    update_vehicle_status,
)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get(
    "/{vehicle_id}",
    response_model=VehicleStateResponse,
    summary="Get a single vehicle by ID",
)
async def get_vehicle_by_id(
    vehicle_id: Annotated[str, Path(min_length=1, max_length=20)],
    session: SessionDep,
) -> VehicleStateResponse:
    try:
        return await get_vehicle(vehicle_id, session)
    except VehicleNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{vehicle_id}/missions",
    response_model=list[MissionResponse],
    summary="Mission history for a vehicle, newest first",
)
async def list_vehicle_missions(
    vehicle_id: Annotated[str, Path(min_length=1, max_length=20)],
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[MissionResponse]:
    try:
        return await get_vehicle_missions(vehicle_id, session, limit=limit, offset=offset)
    except VehicleNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{vehicle_id}/maintenance",
    response_model=list[MaintenanceRecordResponse],
    summary="Maintenance records for a vehicle, newest first",
)
async def list_vehicle_maintenance(
    vehicle_id: Annotated[str, Path(min_length=1, max_length=20)],
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[MaintenanceRecordResponse]:
    try:
        return await get_vehicle_maintenance(
            vehicle_id, session, limit=limit, offset=offset
        )
    except VehicleNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/{vehicle_id}/status",
    response_model=StatusUpdateResponse,
    summary="Update vehicle status; fault cancels active mission",
)
async def patch_vehicle_status(
    vehicle_id: Annotated[str, Path(min_length=1, max_length=20)],
    body: StatusUpdateRequest,
    session: SessionDep,
) -> StatusUpdateResponse:
    try:
        result = await update_vehicle_status(vehicle_id, body.status, session)
        await session.commit()
        return result
    except VehicleNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

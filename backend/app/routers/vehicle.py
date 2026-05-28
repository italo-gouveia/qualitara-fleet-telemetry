from fastapi import APIRouter, HTTPException, status

from app.database import SessionDep
from app.schemas.vehicle import StatusUpdateRequest, StatusUpdateResponse
from app.services.vehicle import VehicleNotFound, update_vehicle_status

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.patch("/{vehicle_id}/status", response_model=StatusUpdateResponse)
async def patch_vehicle_status(
    vehicle_id: str,
    body: StatusUpdateRequest,
    session: SessionDep,
) -> StatusUpdateResponse:
    try:
        result = await update_vehicle_status(vehicle_id, body.status, session)
        await session.commit()
        return result
    except VehicleNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

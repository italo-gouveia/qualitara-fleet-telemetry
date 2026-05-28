import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import MaintenanceRecord, Mission, VehicleState
from app.schemas.telemetry import VehicleStatus
from app.schemas.vehicle import StatusUpdateResponse

logger = logging.getLogger(__name__)


class VehicleNotFound(Exception):
    def __init__(self, vehicle_id: str) -> None:
        super().__init__(f"Vehicle {vehicle_id!r} not found")
        self.vehicle_id = vehicle_id


async def update_vehicle_status(
    vehicle_id: str, new_status: VehicleStatus, session: AsyncSession
) -> StatusUpdateResponse:
    row = await session.execute(
        select(VehicleState)
        .where(VehicleState.vehicle_id == vehicle_id)
        .with_for_update()
    )
    vehicle = row.scalar_one_or_none()
    if vehicle is None:
        raise VehicleNotFound(vehicle_id)

    vehicle.status = new_status.value
    vehicle.updated_at = datetime.now(UTC)

    if new_status != VehicleStatus.FAULT:
        result = StatusUpdateResponse(
            vehicle_id=vehicle_id,
            status=new_status.value,
            mission_cancelled=False,
        )
    else:
        result = await _handle_fault_transition(vehicle_id, session)

    logger.info(
        "vehicle_status_updated",
        extra={
            "vehicle_id": vehicle_id,
            "new_status": new_status.value,
            "mission_cancelled": result.mission_cancelled,
        },
    )
    return result


async def _handle_fault_transition(
    vehicle_id: str, session: AsyncSession
) -> StatusUpdateResponse:
    mission_row = await session.execute(
        select(Mission)
        .where(Mission.vehicle_id == vehicle_id, Mission.status == "active")
        .with_for_update()
    )
    active_mission = mission_row.scalar_one_or_none()

    if active_mission is None:
        return StatusUpdateResponse(
            vehicle_id=vehicle_id,
            status=VehicleStatus.FAULT.value,
            mission_cancelled=False,
        )

    active_mission.status = "cancelled"
    active_mission.cancelled_at = datetime.now(UTC)

    record = MaintenanceRecord(
        vehicle_id=vehicle_id,
        mission_id=active_mission.id,
        created_at=datetime.now(UTC),
        reason="fault_transition",
    )
    session.add(record)
    await session.flush()

    return StatusUpdateResponse(
        vehicle_id=vehicle_id,
        status=VehicleStatus.FAULT.value,
        mission_cancelled=True,
        maintenance_record_id=record.id,
    )

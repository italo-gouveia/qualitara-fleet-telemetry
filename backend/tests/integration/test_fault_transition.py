from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import MaintenanceRecord, Mission, VehicleState


async def _seed_vehicle(session: AsyncSession, vehicle_id: str) -> None:
    session.add(
        VehicleState(
            vehicle_id=vehicle_id,
            status="moving",
            battery_pct=80,
            lat=37.41,
            lon=-122.08,
            updated_at=datetime.now(UTC),
        )
    )
    await session.flush()


async def _seed_active_mission(session: AsyncSession, vehicle_id: str) -> int:
    mission = Mission(
        vehicle_id=vehicle_id,
        status="active",
        created_at=datetime.now(UTC),
    )
    session.add(mission)
    await session.flush()
    return mission.id  # type: ignore[return-value]


@pytest.mark.asyncio
async def test_fault_transition_cancels_active_mission(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    vid = "v-fault-1"
    await _seed_vehicle(db_session, vid)
    mission_id = await _seed_active_mission(db_session, vid)
    await db_session.commit()

    response = await client.patch(f"/vehicles/{vid}/status", json={"status": "fault"})
    assert response.status_code == 200
    body = response.json()
    assert body["mission_cancelled"] is True

    db_session.expire_all()
    result = await db_session.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one()
    assert mission.status == "cancelled"
    assert mission.cancelled_at is not None


@pytest.mark.asyncio
async def test_fault_transition_creates_maintenance_record(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    vid = "v-fault-2"
    await _seed_vehicle(db_session, vid)
    await _seed_active_mission(db_session, vid)
    await db_session.commit()

    response = await client.patch(f"/vehicles/{vid}/status", json={"status": "fault"})
    assert response.status_code == 200
    body = response.json()
    assert body["maintenance_record_id"] is not None

    db_session.expire_all()
    result = await db_session.execute(
        select(MaintenanceRecord).where(MaintenanceRecord.vehicle_id == vid)
    )
    record = result.scalar_one()
    assert record.reason == "fault_transition"


@pytest.mark.asyncio
async def test_fault_transition_no_active_mission_succeeds(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    vid = "v-fault-3"
    await _seed_vehicle(db_session, vid)
    await db_session.commit()

    response = await client.patch(f"/vehicles/{vid}/status", json={"status": "fault"})
    assert response.status_code == 200
    body = response.json()
    assert body["mission_cancelled"] is False
    assert body["maintenance_record_id"] is None


@pytest.mark.asyncio
async def test_fault_transition_idempotent(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    vid = "v-fault-4"
    await _seed_vehicle(db_session, vid)
    await _seed_active_mission(db_session, vid)
    await db_session.commit()

    await client.patch(f"/vehicles/{vid}/status", json={"status": "fault"})
    await client.patch(f"/vehicles/{vid}/status", json={"status": "fault"})

    db_session.expire_all()
    result = await db_session.execute(
        select(MaintenanceRecord).where(MaintenanceRecord.vehicle_id == vid)
    )
    records = result.scalars().all()
    assert len(records) == 1


@pytest.mark.asyncio
async def test_non_fault_status_update_no_side_effects(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    vid = "v-fault-5"
    await _seed_vehicle(db_session, vid)
    await _seed_active_mission(db_session, vid)
    await db_session.commit()

    response = await client.patch(f"/vehicles/{vid}/status", json={"status": "idle"})
    assert response.status_code == 200
    body = response.json()
    assert body["mission_cancelled"] is False

    db_session.expire_all()
    result = await db_session.execute(
        select(MaintenanceRecord).where(MaintenanceRecord.vehicle_id == vid)
    )
    assert result.scalars().first() is None


@pytest.mark.asyncio
async def test_fault_transition_vehicle_not_found_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.patch("/vehicles/v-nonexistent/status", json={"status": "fault"})
    assert response.status_code == 404

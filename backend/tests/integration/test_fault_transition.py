from datetime import UTC, datetime, timedelta

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


@pytest.mark.asyncio
async def test_get_vehicle_missions_returns_list(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    vid = "v-missions-1"
    await _seed_vehicle(db_session, vid)
    await _seed_active_mission(db_session, vid)
    await db_session.commit()

    await client.patch(f"/vehicles/{vid}/status", json={"status": "fault"})

    response = await client.get(f"/vehicles/{vid}/missions")
    assert response.status_code == 200
    missions = response.json()
    assert len(missions) >= 1
    assert missions[0]["vehicle_id"] == vid
    assert missions[0]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_get_vehicle_missions_not_found_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.get("/vehicles/v-no-such/missions")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_vehicle_maintenance_returns_list(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    vid = "v-maint-1"
    await _seed_vehicle(db_session, vid)
    await _seed_active_mission(db_session, vid)
    await db_session.commit()

    await client.patch(f"/vehicles/{vid}/status", json={"status": "fault"})

    response = await client.get(f"/vehicles/{vid}/maintenance")
    assert response.status_code == 200
    records = response.json()
    assert len(records) >= 1
    assert records[0]["vehicle_id"] == vid
    assert records[0]["reason"] == "fault_transition"


@pytest.mark.asyncio
async def test_get_vehicle_maintenance_not_found_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.get("/vehicles/v-no-such/maintenance")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH status — non-fault paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("new_status", ["idle", "moving", "charging"])
async def test_patch_non_fault_status_updates_vehicle_row(
    client: AsyncClient, db_session: AsyncSession, new_status: str
) -> None:
    """PATCH to any non-fault status must update the DB row and return the new status."""
    vid = f"v-nonfault-{new_status}"
    await _seed_vehicle(db_session, vid)
    await db_session.commit()

    response = await client.patch(f"/vehicles/{vid}/status", json={"status": new_status})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == new_status
    assert body["mission_cancelled"] is False
    assert body["maintenance_record_id"] is None

    db_session.expire_all()
    result = await db_session.execute(
        select(VehicleState).where(VehicleState.vehicle_id == vid)
    )
    assert result.scalar_one().status == new_status


# ---------------------------------------------------------------------------
# Missions — pagination and ordering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_vehicle_missions_pagination_limit(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """limit param must cap the number of missions returned."""
    vid = "v-missions-pag-limit"
    await _seed_vehicle(db_session, vid)
    for _ in range(3):
        await _seed_active_mission(db_session, vid)
    await db_session.commit()

    response = await client.get(f"/vehicles/{vid}/missions?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_vehicle_missions_pagination_offset(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """offset param must skip the first N missions."""
    vid = "v-miss-pag-off"
    await _seed_vehicle(db_session, vid)
    for _ in range(3):
        await _seed_active_mission(db_session, vid)
    await db_session.commit()

    response = await client.get(f"/vehicles/{vid}/missions?offset=2")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_vehicle_missions_ordered_newest_first(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Missions must be returned newest-first (descending created_at)."""
    vid = "v-missions-ordered"
    await _seed_vehicle(db_session, vid)
    early = Mission(vehicle_id=vid, status="active", created_at=datetime(2026, 1, 1, tzinfo=UTC))
    late = Mission(vehicle_id=vid, status="active", created_at=datetime(2026, 6, 1, tzinfo=UTC))
    db_session.add(early)
    db_session.add(late)
    await db_session.commit()

    response = await client.get(f"/vehicles/{vid}/missions")
    assert response.status_code == 200
    missions = response.json()
    assert len(missions) == 2
    assert missions[0]["created_at"] > missions[1]["created_at"]


# ---------------------------------------------------------------------------
# Maintenance records — pagination and ordering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_vehicle_maintenance_pagination_limit(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """limit param must cap the number of maintenance records returned."""
    vid = "v-maint-pag-limit"
    await _seed_vehicle(db_session, vid)
    mission_ids = [await _seed_active_mission(db_session, vid) for _ in range(3)]
    for mid in mission_ids:
        db_session.add(
            MaintenanceRecord(
                vehicle_id=vid,
                mission_id=mid,
                created_at=datetime.now(UTC),
                reason="fault_transition",
            )
        )
    await db_session.commit()

    response = await client.get(f"/vehicles/{vid}/maintenance?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_vehicle_maintenance_ordered_newest_first(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Maintenance records must be returned newest-first (descending created_at)."""
    vid = "v-maint-ordered"
    await _seed_vehicle(db_session, vid)
    mission_ids = [await _seed_active_mission(db_session, vid) for _ in range(2)]
    for i, mid in enumerate(mission_ids):
        db_session.add(
            MaintenanceRecord(
                vehicle_id=vid,
                mission_id=mid,
                created_at=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=i),
                reason="fault_transition",
            )
        )
    await db_session.commit()

    response = await client.get(f"/vehicles/{vid}/maintenance")
    assert response.status_code == 200
    records = response.json()
    assert len(records) == 2
    assert records[0]["created_at"] > records[1]["created_at"]

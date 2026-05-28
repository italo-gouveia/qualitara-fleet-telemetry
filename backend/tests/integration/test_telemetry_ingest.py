import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anomaly import Anomaly
from app.models.telemetry import TelemetryEvent
from app.models.vehicle import VehicleState
from app.models.zone import ZoneCount
from tests.helpers import make_event

EXPECTED_ZONE_COUNT = 20  # all zone rows in the seeded DB


@pytest.mark.asyncio
async def test_ingest_valid_event_returns_201(client: AsyncClient) -> None:
    response = await client.post("/telemetry", json=make_event())
    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert body["anomalies_detected"] == 0


@pytest.mark.asyncio
async def test_ingest_creates_vehicle_state_row(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await client.post("/telemetry", json=make_event(vehicle_id="v-99"))

    result = await db_session.execute(
        select(VehicleState).where(VehicleState.vehicle_id == "v-99")
    )
    state = result.scalar_one_or_none()
    assert state is not None
    assert state.status == "moving"
    assert state.battery_pct == 80


@pytest.mark.asyncio
async def test_ingest_zone_entered_increments_counter(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    zone = "inbound_dock_a"
    before = await db_session.execute(
        select(ZoneCount.entry_count).where(ZoneCount.zone_id == zone)
    )
    count_before = before.scalar_one()

    await client.post("/telemetry", json=make_event(zone_entered=zone))

    db_session.expire_all()
    after = await db_session.execute(
        select(ZoneCount.entry_count).where(ZoneCount.zone_id == zone)
    )
    assert after.scalar_one() == count_before + 1


@pytest.mark.asyncio
async def test_ingest_low_battery_creates_anomaly(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    payload = make_event(vehicle_id="v-low-bat", battery_pct=10)
    response = await client.post("/telemetry", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["anomalies_detected"] >= 1

    result = await db_session.execute(
        select(Anomaly).where(Anomaly.vehicle_id == "v-low-bat")
    )
    anomalies = result.scalars().all()
    types = {a.type for a in anomalies}
    assert "low_battery" in types


@pytest.mark.asyncio
async def test_ingest_invalid_battery_pct_returns_422(client: AsyncClient) -> None:
    response = await client.post("/telemetry", json=make_event(battery_pct=150))
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_persists_telemetry_event_row(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    payload = make_event(vehicle_id="v-persist", speed_mps=2.5)
    response = await client.post("/telemetry", json=payload)
    event_id = response.json()["id"]

    result = await db_session.execute(
        select(TelemetryEvent).where(TelemetryEvent.id == event_id)
    )
    row = result.scalar_one()
    assert row.vehicle_id == "v-persist"
    assert row.speed_mps == 2.5


@pytest.mark.asyncio
async def test_ingest_zone_entered_none_does_not_increment_any_counter(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """An event with zone_entered=None must not modify any zone counter row."""
    before = await db_session.execute(select(ZoneCount))
    counts_before = {row.zone_id: row.entry_count for row in before.scalars().all()}

    await client.post("/telemetry", json=make_event(vehicle_id="v-nozone", zone_entered=None))

    db_session.expire_all()
    after = await db_session.execute(select(ZoneCount))
    counts_after = {row.zone_id: row.entry_count for row in after.scalars().all()}

    assert counts_before == counts_after


@pytest.mark.asyncio
async def test_ingest_multiple_anomalies_single_event(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """An event violating multiple rules creates one anomaly row per triggered rule.

    battery_pct=3  →  low_battery + critical_battery
    status=fault   →  fault_entered
    error_codes    →  error_code_reported
    Total: 4 anomalies
    """
    payload = make_event(
        vehicle_id="v-multi-anomaly",
        battery_pct=3,
        status="fault",
        error_codes=["E001"],
    )
    response = await client.post("/telemetry", json=payload)
    assert response.status_code == 201
    assert response.json()["anomalies_detected"] == 4

    result = await db_session.execute(
        select(Anomaly).where(Anomaly.vehicle_id == "v-multi-anomaly")
    )
    types = {a.type for a in result.scalars().all()}
    assert types == {"low_battery", "critical_battery", "fault_entered", "error_code_reported"}

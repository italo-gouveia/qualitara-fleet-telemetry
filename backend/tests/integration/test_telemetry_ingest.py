import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anomaly import Anomaly
from app.models.telemetry import TelemetryEvent
from app.models.vehicle import VehicleState
from app.models.zone import ZoneCount
from tests.helpers import make_event


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

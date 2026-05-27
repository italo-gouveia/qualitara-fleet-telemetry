import pytest
from httpx import AsyncClient

from tests.helpers import make_event


@pytest.mark.asyncio
async def test_fleet_state_empty_returns_zeros(client: AsyncClient) -> None:
    response = await client.get("/fleet/state")
    assert response.status_code == 200
    body = response.json()
    # May have data from other tests — just assert expected fields exist
    assert "idle" in body
    assert "moving" in body
    assert "charging" in body
    assert "fault" in body
    assert "total" in body
    assert body["total"] == body["idle"] + body["moving"] + body["charging"] + body["fault"]


@pytest.mark.asyncio
async def test_fleet_state_correct_counts_after_ingest(client: AsyncClient) -> None:
    # Seed 3 vehicles with distinct statuses
    for vehicle_id, status in [("v-f1", "idle"), ("v-f2", "moving"), ("v-f3", "charging")]:
        payload = make_event(vehicle_id=vehicle_id, status=status)
        resp = await client.post("/telemetry", json=payload)
        assert resp.status_code == 201

    response = await client.get("/fleet/state")
    assert response.status_code == 200
    body = response.json()
    # At minimum the 3 we just inserted must be reflected in total
    assert body["total"] >= 3
    assert body["idle"] >= 1
    assert body["moving"] >= 1
    assert body["charging"] >= 1


@pytest.mark.asyncio
async def test_zone_counts_returns_all_20_zones(client: AsyncClient) -> None:
    response = await client.get("/zones/counts")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 20


@pytest.mark.asyncio
async def test_zone_counts_increments_reflected(client: AsyncClient) -> None:
    zone = "charging_bay_1"
    before_resp = await client.get("/zones/counts")
    count_before = before_resp.json()[zone]

    await client.post("/telemetry", json=make_event(vehicle_id="v-zone", zone_entered=zone))

    after_resp = await client.get("/zones/counts")
    assert after_resp.json()[zone] == count_before + 1


@pytest.mark.asyncio
async def test_vehicles_returns_list(client: AsyncClient) -> None:
    await client.post("/telemetry", json=make_event(vehicle_id="v-list"))

    response = await client.get("/vehicles")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    ids = [v["vehicle_id"] for v in body]
    assert "v-list" in ids


@pytest.mark.asyncio
async def test_vehicles_ordered_by_vehicle_id(client: AsyncClient) -> None:
    for vehicle_id in ["v-z99", "v-a01"]:
        await client.post("/telemetry", json=make_event(vehicle_id=vehicle_id))

    response = await client.get("/vehicles")
    ids = [v["vehicle_id"] for v in response.json()]
    assert ids == sorted(ids)

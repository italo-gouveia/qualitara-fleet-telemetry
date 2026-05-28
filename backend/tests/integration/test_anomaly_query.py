from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from tests.helpers import make_event

_BASE_TS = "2026-05-01T10:00:00Z"
_LOW_BAT = 10  # triggers low_battery anomaly


@pytest.mark.asyncio
async def test_anomaly_query_no_filters_returns_all(client: AsyncClient) -> None:
    for vid in ["v-an1", "v-an2"]:
        await client.post("/telemetry", json=make_event(vehicle_id=vid, battery_pct=_LOW_BAT))

    response = await client.get("/anomalies")
    assert response.status_code == 200
    body = response.json()
    ids = {a["vehicle_id"] for a in body}
    assert "v-an1" in ids
    assert "v-an2" in ids


@pytest.mark.asyncio
async def test_anomaly_query_vehicle_filter(client: AsyncClient) -> None:
    await client.post("/telemetry", json=make_event(vehicle_id="v-an-filter", battery_pct=_LOW_BAT))
    await client.post("/telemetry", json=make_event(vehicle_id="v-an-other", battery_pct=_LOW_BAT))

    response = await client.get("/anomalies", params={"vehicle_id": "v-an-filter"})
    assert response.status_code == 200
    body = response.json()
    assert all(a["vehicle_id"] == "v-an-filter" for a in body)
    assert len(body) >= 1


@pytest.mark.asyncio
async def test_anomaly_query_time_range_filters_correctly(client: AsyncClient) -> None:
    await client.post("/telemetry", json=make_event(vehicle_id="v-an-time", battery_pct=_LOW_BAT))

    now = datetime.now(UTC)
    start = (now - timedelta(minutes=5)).isoformat()
    end = (now + timedelta(minutes=5)).isoformat()

    response = await client.get("/anomalies", params={"start": start, "end": end})
    assert response.status_code == 200
    body = response.json()
    vids = {a["vehicle_id"] for a in body}
    assert "v-an-time" in vids


@pytest.mark.asyncio
async def test_anomaly_query_outside_range_returns_empty(client: AsyncClient) -> None:
    await client.post("/telemetry", json=make_event(vehicle_id="v-an-old", battery_pct=_LOW_BAT))

    far_past_start = "2020-01-01T00:00:00Z"
    far_past_end = "2020-01-02T00:00:00Z"

    response = await client.get(
        "/anomalies",
        params={"vehicle_id": "v-an-old", "start": far_past_start, "end": far_past_end},
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_anomaly_query_limit_respected(client: AsyncClient) -> None:
    for i in range(5):
        await client.post(
            "/telemetry",
            json=make_event(vehicle_id=f"v-an-lim-{i}", battery_pct=_LOW_BAT),
        )

    response = await client.get("/anomalies", params={"limit": 2})
    assert response.status_code == 200
    assert len(response.json()) <= 2


@pytest.mark.asyncio
async def test_anomaly_query_offset_skips_first_result(client: AsyncClient) -> None:
    vid = "v-an-offset"
    # Two telemetry events → two anomalies for the same vehicle
    await client.post("/telemetry", json=make_event(vehicle_id=vid, battery_pct=_LOW_BAT))
    await client.post("/telemetry", json=make_event(vehicle_id=vid, battery_pct=_LOW_BAT))

    all_response = await client.get("/anomalies", params={"vehicle_id": vid, "limit": 10})
    all_ids = [a["id"] for a in all_response.json()]
    assert len(all_ids) >= 2

    offset_response = await client.get(
        "/anomalies", params={"vehicle_id": vid, "limit": 10, "offset": 1}
    )
    offset_ids = [a["id"] for a in offset_response.json()]
    # Offset=1 must skip the first result
    assert offset_ids == all_ids[1:]

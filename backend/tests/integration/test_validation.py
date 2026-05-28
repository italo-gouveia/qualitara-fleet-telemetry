"""Contract tests: invalid inputs must return 422 Unprocessable Entity."""

import pytest
from httpx import AsyncClient

from tests.helpers import make_event


@pytest.mark.asyncio
async def test_telemetry_empty_vehicle_id_returns_422(client: AsyncClient) -> None:
    response = await client.post("/telemetry", json=make_event(vehicle_id=""))
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_telemetry_vehicle_id_too_long_returns_422(client: AsyncClient) -> None:
    response = await client.post("/telemetry", json=make_event(vehicle_id="x" * 21))
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_vehicles_limit_zero_returns_422(client: AsyncClient) -> None:
    response = await client.get("/vehicles?limit=0")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_vehicles_limit_over_max_returns_422(client: AsyncClient) -> None:
    response = await client.get("/vehicles?limit=101")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_anomalies_vehicle_id_too_long_returns_422(client: AsyncClient) -> None:
    response = await client.get(f"/anomalies?vehicle_id={'x' * 21}")
    assert response.status_code == 422

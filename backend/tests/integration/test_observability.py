"""Tests for observability contracts: exception handler, X-Request-Id, Prometheus, health."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.main import app


@pytest.mark.asyncio
async def test_unhandled_exception_returns_500_with_safe_body(
    db_session: AsyncSession,
) -> None:
    """Global exception handler must return 500 with a generic message — no stack trace.

    Uses raise_app_exceptions=False so the transport returns the 500 response
    instead of re-raising the server-side exception (default test behaviour).
    """

    async def _override() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = _override
    try:
        with patch("app.routers.fleet.get_fleet_state", new_callable=AsyncMock) as mock:
            mock.side_effect = RuntimeError("unexpected internal error")
            transport = ASGITransport(app=app, raise_app_exceptions=False)  # type: ignore[arg-type]
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/fleet/state")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "An unexpected error occurred. Please try again later."
    assert "RuntimeError" not in response.text
    assert "traceback" not in response.text.lower()


@pytest.mark.asyncio
async def test_response_always_includes_request_id_header(client: AsyncClient) -> None:
    """Every response must carry X-Request-Id for log correlation."""
    response = await client.get("/health")
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_provided_request_id_is_echoed_back(client: AsyncClient) -> None:
    """If the client sends X-Request-Id, the same value must be returned."""
    correlation_id = "test-correlation-id-abc123"
    response = await client.get("/health", headers={"X-Request-Id": correlation_id})
    assert response.headers["x-request-id"] == correlation_id


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_format(client: AsyncClient) -> None:
    """GET /metrics must expose Prometheus text format with request counters."""
    # Trigger at least one request so counters are non-empty
    await client.get("/health")
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


@pytest.mark.asyncio
async def test_health_returns_ok_when_db_is_up(client: AsyncClient) -> None:
    """Health endpoint must return 200 {"status": "ok"} when DB is reachable."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Integration Testing Guide

## Architecture Overview

```
pytest
  └── AsyncClient (httpx, ASGI transport)
        └── FastAPI app
              └── AsyncSession (SQLAlchemy async)
                    └── SQLite in-memory (aiosqlite)
```

No running server, no network calls — the full stack in process, wiped between tests.

## Required Dependencies

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"

[project.optional-dependencies]
test = [
  "pytest>=8",
  "pytest-asyncio>=0.23",
  "httpx>=0.27",
  "aiosqlite>=0.20",
]
```

## conftest.py Pattern

```python
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import get_session, Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="session")
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)

@pytest.fixture
async def db_session(session_factory):
    async with session_factory() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    async def override_get_session():
        yield db_session
    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

## Writing a Test

```python
async def test_ingest_creates_telemetry_event(client, db_session):
    payload = {
        "vehicle_id": "v-01",
        "timestamp": "2026-05-27T10:00:00Z",
        "lat": 37.41, "lon": -122.08,
        "battery_pct": 80, "speed_mps": 1.2,
        "status": "moving",
        "error_codes": [],
        "zone_entered": None,
    }
    response = await client.post("/telemetry", json=payload)
    assert response.status_code == 201

    result = await db_session.execute(
        select(TelemetryEvent).where(TelemetryEvent.vehicle_id == "v-01")
    )
    event = result.scalar_one()
    assert event.battery_pct == 80
```

## Concurrency Tests

SQLite in-memory does not support true concurrent writers. For the zone counter concurrency test, use one of:
1. Sequential calls in a loop (proves logic, not OS-level concurrency).
2. PostgreSQL via `asyncpg` with `asyncio.gather()` — requires a test DB service.

Document which approach is used in the test file.

```python
async def test_zone_counter_increments_correctly(client):
    # Sequential simulation of 10 arrivals in same zone
    for _ in range(10):
        await client.post("/telemetry", json={**BASE_EVENT, "zone_entered": "charging_bay_1"})

    response = await client.get("/zones/counts")
    counts = response.json()
    assert counts["charging_bay_1"] == 10
```

## Seed Helpers

```python
# tests/helpers.py
def make_event(**overrides) -> dict:
    base = {
        "vehicle_id": "v-01",
        "timestamp": "2026-05-27T10:00:00Z",
        "lat": 0.0, "lon": 0.0,
        "battery_pct": 80, "speed_mps": 1.0,
        "status": "moving",
        "error_codes": [],
        "zone_entered": None,
    }
    return {**base, **overrides}
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ScopeMismatch` | session fixture scope higher than test | use `scope="function"` for db_session |
| `DetachedInstanceError` | `expire_on_commit=True` default | set `expire_on_commit=False` in session factory |
| `greenlet_spawn` error | sync code inside async context | ensure all DB calls are `await`-ed |
| Tables not found | `create_all` not called | check engine fixture scope is `session` and runs before first test |

# Testing Rules

## Goals

- Prove the behaviors the challenge cares about: concurrent ingest, zone counting, fault transition atomicity, anomaly detection, and all three response shapes.
- Tests are fast and deterministic — no live DB required for unit tests; SQLite in-memory for most integration tests.

## Test Structure

```
backend/tests/
├── unit/
│   ├── test_anomaly_rules.py      # pure function tests — no DB, no HTTP
│   ├── test_schemas.py            # Pydantic validation edge cases
│   └── test_zone_logic.py
└── integration/
    ├── conftest.py                # app fixture, DB setup, session override
    ├── test_telemetry_ingest.py   # POST /telemetry happy + edge paths
    ├── test_zone_counts.py        # GET /zones/counts; concurrent increment
    ├── test_fault_transition.py   # PATCH /vehicles/{id}/status → fault
    ├── test_fleet_state.py        # GET /fleet/state aggregate
    └── test_anomaly_queries.py    # GET /anomalies?vehicle_id=&start=&end=
```

## Naming Convention

`test_<subject>_<condition>_<expected>`

```python
def test_ingest_valid_event_returns_201(): ...
def test_ingest_fault_status_cancels_active_mission(): ...
def test_zone_counter_concurrent_increments_all_counted(): ...
def test_anomaly_low_battery_triggers_anomaly_record(): ...
def test_fleet_state_returns_per_status_counts(): ...
```

## Integration Test Setup

```python
# conftest.py
@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def session(engine):
    async with AsyncSession(engine) as s:
        yield s
        await s.rollback()  # clean up after each test

@pytest.fixture
async def client(session):
    app.dependency_overrides[get_session] = lambda: session
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

- Roll back after each test — never truncate tables.
- Seed only what the test needs; use small, explicit builders.

## Key Tests to Include

1. **Happy path ingest**: valid event → 201, `telemetry_events` row created, `vehicle_states` upserted.
2. **Anomaly detection**: event with `battery_pct < 15` → anomaly row created with type `low_battery`.
3. **Zone counter**: 10 concurrent `POST /telemetry` with `zone_entered = "charging_bay_1"` → `entry_count == 10`.
4. **Fault transition**: vehicle with active mission → `PATCH status=fault` → mission `cancelled`, maintenance record created; idempotent (second call is a no-op).
5. **Fleet aggregate**: 3 vehicles in different statuses → `GET /fleet/state` returns correct counts.
6. **Anomaly filter**: anomaly at time T → query with `start=T-1s&end=T+1s` returns it; outside range returns empty.

## Unit Test Rules

- Import only the function under test; no FastAPI, no DB.
- Use `pytest.mark.parametrize` for boundary cases:
  ```python
  @pytest.mark.parametrize("battery,expected", [(15, False), (14, True), (0, True)])
  def test_low_battery_rule(battery, expected): ...
  ```

## CI Alignment

```bash
pytest tests/unit/ -v                       # fast, no fixtures
pytest tests/integration/ -v --asyncio-mode=auto  # needs DB
```

- All tests must pass before merge.
- `ruff check . && mypy .` must also pass.

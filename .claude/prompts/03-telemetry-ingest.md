# Prompt 03 — Telemetry Ingest Endpoint

## Goal

Implement `POST /telemetry` — the core ingest path. This is the most complex endpoint: it writes a telemetry event, upserts vehicle state, increments zone counter (if applicable), and detects anomalies — all in one transaction.

## Context to Read

- `.claude/rules/database.md` — atomic increment pattern, upsert
- `.claude/context/domain-model.md` — anomaly rules
- `.claude/rules/testing.md` — test naming and structure
- Agent: `senior-python-developer`

## Schema

**Request** (`schemas/telemetry.py`):
```python
class TelemetryEventIn(BaseModel):
    vehicle_id: str
    timestamp: datetime
    lat: float
    lon: float
    battery_pct: Annotated[int, Field(ge=0, le=100)]
    speed_mps: Annotated[float, Field(ge=0)]
    status: VehicleStatus
    error_codes: list[str] = []
    zone_entered: str | None = None
```

**Response**: `{"id": <int>, "anomalies_detected": <int>}`, status 201.

## Service Logic (`services/telemetry.py`)

```python
async def ingest_event(event: TelemetryEventIn, session: AsyncSession) -> IngestResult:
    async with session.begin():
        # 1. Insert TelemetryEvent
        # 2. Upsert VehicleState
        # 3. If zone_entered: atomic increment ZoneCount
        # 4. Run anomaly rules → insert Anomaly rows
        # 5. If status == fault: handle fault transition (see Prompt 05)
    return IngestResult(id=event_id, anomalies_detected=len(anomalies))
```

## Zone Counter (MUST be atomic)

```python
await session.execute(
    update(ZoneCount)
    .where(ZoneCount.zone_id == event.zone_entered)
    .values(entry_count=ZoneCount.entry_count + 1, last_updated=func.now())
)
```

**Never** do: `zone = await get_zone(…); zone.entry_count += 1`.

## Anomaly Rules (`core/anomaly.py`)

Implement as a list of pure functions:
```python
ANOMALY_RULES: list[Callable[[TelemetryEventIn], AnomalyType | None]] = [
    check_low_battery,       # battery_pct < 15
    check_critical_battery,  # battery_pct < 5
    check_fault_entered,     # status == fault
    check_speed_anomaly,     # speed_mps > 0.5 and status == idle
    check_error_codes,       # len(error_codes) > 0
]
```

Each function: `(event: TelemetryEventIn) -> AnomalyType | None`

## Tests to Write

1. `test_ingest_valid_event_returns_201`
2. `test_ingest_creates_vehicle_state_row`
3. `test_ingest_zone_entered_increments_counter`
4. `test_ingest_low_battery_creates_anomaly`
5. `test_ingest_invalid_battery_pct_returns_422`

## Acceptance Criteria

- `POST /telemetry` with valid payload → 201
- Zone counter incremented exactly once per event with `zone_entered` set
- Anomaly created for `battery_pct=10`
- `pytest tests/integration/test_telemetry_ingest.py` all pass

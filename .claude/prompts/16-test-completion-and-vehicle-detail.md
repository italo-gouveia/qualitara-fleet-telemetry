# Prompt 16 — Test Completion and Vehicle Detail Endpoint

## Context

Two visible gaps remain before submission:
1. `tests/unit/` has only `__init__.py` — no unit tests at all.
2. Several validation contracts added in Prompt 14 have no tests, and the
   `GET /vehicles` pagination only tests `limit`, not `offset`.
3. There is no single-vehicle lookup endpoint (`GET /vehicles/{vehicle_id}`),
   which any dashboard will call on row-click.

## Goal

Close all three gaps in a single pass: fill the unit test folder, add missing
contract tests, and deliver `GET /vehicles/{vehicle_id}`.

---

## Deliverable 1 — Unit tests for anomaly rules

File: `backend/tests/unit/test_anomaly_rules.py`

Create a local `make_event(**overrides)` helper returning a `TelemetryEventIn`
model (not a dict) with safe defaults:
- `vehicle_id="v-test"`, `timestamp=datetime.now(UTC)`, `lat=0.0`, `lon=0.0`,
  `battery_pct=80`, `speed_mps=1.0`, `status=VehicleStatus.MOVING`,
  `error_codes=[]`, `zone_entered=None`.

Test each rule function individually at boundary values:

| Rule | Cases |
|------|-------|
| `check_low_battery` | `battery_pct=14` → LOW_BATTERY; `battery_pct=15` → None; `battery_pct=80` → None |
| `check_critical_battery` | `battery_pct=4` → CRITICAL_BATTERY; `battery_pct=5` → None |
| `check_fault_entered` | `status=FAULT` → FAULT_ENTERED; `status=IDLE` → None |
| `check_speed_anomaly` | `speed=0.6, status=IDLE` → SPEED_ANOMALY; `speed=0.5, status=IDLE` → None; `speed=1.0, status=MOVING` → None |
| `check_error_codes` | `error_codes=["E01"]` → ERROR_CODE_REPORTED; `error_codes=[]` → None |
| `ANOMALY_RULES` pipeline | verify list has exactly 5 rules; a multi-anomaly event (battery_pct=4, status=FAULT, error_codes=["E01"]) yields ≥3 detected anomalies |

---

## Deliverable 2 — Validation contract tests

File: `backend/tests/integration/test_validation.py`

Test that invalid inputs are rejected with 422 end-to-end:

- `POST /telemetry` with `vehicle_id=""` → 422
- `POST /telemetry` with `vehicle_id="x" * 21` → 422
- `GET /vehicles?limit=0` → 422
- `GET /vehicles?limit=101` → 422
- `GET /anomalies?vehicle_id=${"x" * 21}` → 422

---

## Deliverable 3 — Offset pagination test

Add to `backend/tests/integration/test_fleet_endpoints.py`:

`test_vehicles_pagination_offset` — seed vehicles `v-off-a`, `v-off-b`, `v-off-c`
(alphabetical order guaranteed). Assert:
- `GET /vehicles?limit=1&offset=0` → `vehicle_id == "v-off-a"`
- `GET /vehicles?limit=1&offset=1` → `vehicle_id == "v-off-b"`

---

## Deliverable 4 — `GET /vehicles/{vehicle_id}` endpoint

### Repository — `backend/app/repositories/vehicle_repository.py`

```python
async def get_vehicle_by_id(
    vehicle_id: str, session: AsyncSession
) -> VehicleStateResponse | None:
```
Returns a `VehicleStateResponse` or `None` if not found.

### Service — `backend/app/services/vehicle.py`

```python
async def get_vehicle(
    vehicle_id: str, session: AsyncSession
) -> VehicleStateResponse:
```
Calls `get_vehicle_by_id`; raises `VehicleNotFound` if `None`.

### Router — `backend/app/routers/vehicle.py`

```
GET /vehicles/{vehicle_id}
response_model=VehicleStateResponse
summary="Get a single vehicle by ID"
```
Returns 200 or 404 using the existing `VehicleNotFound` → HTTPException pattern.

### Integration tests — `backend/tests/integration/test_fleet_endpoints.py`

- `test_get_vehicle_by_id_returns_state` — ingest event, GET `/vehicles/v-detail` → 200 + correct `vehicle_id`
- `test_get_vehicle_by_id_not_found` — GET `/vehicles/v-missing` → 404

---

## Acceptance criteria

- [ ] `tests/unit/test_anomaly_rules.py` covers all 5 rules + pipeline
- [ ] `tests/integration/test_validation.py` has 5 422-contract tests
- [ ] `test_vehicles_pagination_offset` in `test_fleet_endpoints.py`
- [ ] `GET /vehicles/{vehicle_id}` returns 200 or 404
- [ ] Two integration tests for the new endpoint
- [ ] `pytest -v` all green (target ≥38 tests)
- [ ] `ruff check .` / `mypy app/` clean

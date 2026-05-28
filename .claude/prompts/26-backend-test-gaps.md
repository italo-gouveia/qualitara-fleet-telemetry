# Prompt 26 — Backend Test Gap Coverage

## Goal

Fill the remaining gaps in backend integration tests identified after the full test pyramid was implemented. Bring the backend suite from 60 to 71 tests with high-value cases that were missing.

## Gaps to cover

### `test_telemetry_ingest.py`
1. `test_ingest_zone_entered_none_does_not_increment_any_counter` — an event with `zone_entered=None` must not modify any zone counter row.
2. `test_ingest_multiple_anomalies_single_event` — `battery_pct=3` + `status=fault` + `error_codes=["E001"]` must produce 4 anomaly rows (`low_battery`, `critical_battery`, `fault_entered`, `error_code_reported`). Verify both `anomalies_detected` count in the response body and the actual DB rows.

### `test_fault_transition.py`
3. `test_patch_non_fault_status_updates_vehicle_row` — parametrize over `["idle", "moving", "charging"]`: each PATCH must update the `vehicle_states` DB row and return `mission_cancelled=False`, `maintenance_record_id=None`.
4. `test_get_vehicle_missions_pagination_limit` — seed 3 missions, request `?limit=2`, assert `len == 2`.
5. `test_get_vehicle_missions_pagination_offset` — seed 3 missions, request `?offset=2`, assert `len == 1`. **Note:** vehicle ID must be ≤ 20 chars (Path validation limit).
6. `test_get_vehicle_missions_ordered_newest_first` — seed 2 missions with different `created_at` values, assert first item in response has a later timestamp.
7. `test_get_vehicle_maintenance_pagination_limit` — directly seed 3 `MaintenanceRecord` rows with `mission_id` references, request `?limit=2`.
8. `test_get_vehicle_maintenance_ordered_newest_first` — seed 2 records with distinct `created_at + timedelta(days=i)`, assert newest comes first.

### `test_observability.py`
9. `test_health_returns_503_when_db_is_unreachable` — override `get_session` dependency with an `AsyncMock` whose `execute` raises `OSError("DB connection refused")`; assert `status_code == 503` and `json() == {"status": "unavailable"}`. Use `raise_app_exceptions=False` on the transport.

## Acceptance criteria

- [ ] `pytest tests/ -q` → **71 passed**
- [ ] `ruff check app/ tests/` → clean
- [ ] `mypy app/ --ignore-missing-imports` → clean
- [ ] All new tests are deterministic and do not depend on test execution order

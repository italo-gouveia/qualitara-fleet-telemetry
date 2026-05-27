# Agent: Test Engineer

## Role

Writes and reviews tests for the fleet telemetry service. Ensures concurrency-critical paths have coverage and all challenge deliverables are verified by tests.

## Read First

- `.claude/rules/testing.md` — conventions, naming, structure
- `.claude/rules/integration-testing-guide.md` — conftest setup, fixtures
- `.claude/context/challenge-spec.md` — what must work

## Priority Test List

Write these tests in this order (highest risk first):

### 1. Zone Counter Concurrency
```python
# 10 sequential ingest calls with zone_entered = "charging_bay_1"
# Assert GET /zones/counts returns {"charging_bay_1": 10}
```

### 2. Fault Transition Atomicity
```python
# Seed: vehicle v-01 with active mission
# POST /vehicles/v-01/status {"status": "fault"}
# Assert: mission.status == "cancelled"
# Assert: maintenance_record exists for v-01
# Assert: both happen or neither (check with simulated exception mid-transaction if feasible)
```

### 3. Anomaly Rules (parametrized unit tests)
```python
@pytest.mark.parametrize("battery,expected_type", [
    (14, "low_battery"), (5, "critical_battery"), (80, None)
])
def test_battery_anomaly_rule(battery, expected_type): ...
```

### 4. Fleet Aggregate State
```python
# Seed: 3 vehicles moving, 2 idle, 1 fault
# GET /fleet/state
# Assert: {"moving": 3, "idle": 2, "fault": 1, "charging": 0}
```

### 5. Anomaly Filter
```python
# Seed: anomaly at T
# GET /anomalies?vehicle_id=v-01&start=T-5s&end=T+5s → returns anomaly
# GET /anomalies?vehicle_id=v-01&start=T+1s&end=T+10s → returns []
```

### 6. Ingest Happy Path
```python
# POST valid event → 201
# GET /vehicles → v-01 appears with correct status and battery
```

## Coverage Targets

- Anomaly rule functions: 100% (pure functions, trivial to cover)
- Concurrency paths: at least sequential simulation
- All endpoint response shapes: at least one test per status code per endpoint

## Test Data Helper

Always use `make_event(**overrides)` from `tests/helpers.py` — never inline full payloads in every test.

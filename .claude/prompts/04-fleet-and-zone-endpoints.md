# Prompt 04 — Fleet State and Zone Count Endpoints

## Goal

Implement the read endpoints: `GET /fleet/state`, `GET /zones/counts`, `GET /vehicles`.

## Endpoints

### `GET /fleet/state`
Returns per-status counts across all vehicles.

```json
{
  "idle": 10,
  "moving": 30,
  "charging": 8,
  "fault": 2,
  "total": 50
}
```

**Query (MUST use GROUP BY, not in-process counting)**:
```python
result = await session.execute(
    select(VehicleState.status, func.count().label("count"))
    .group_by(VehicleState.status)
)
```

### `GET /zones/counts`
Returns all 20 zones with their entry counts.

```json
{
  "inbound_dock_a": 15,
  "charging_bay_1": 43,
  ...
}
```

Returns all zones (even those with count 0 — seeded on startup).

### `GET /vehicles`
Returns list of all known vehicles (those with at least one telemetry event).

```json
[
  {"vehicle_id": "v-01", "status": "moving", "battery_pct": 78, "lat": 37.41, "lon": -122.08, "updated_at": "..."},
  ...
]
```

Ordered by `vehicle_id`.

## Repositories to Create

**`repositories/vehicle_repository.py`**:
- `get_all_vehicle_states() -> list[VehicleState]`
- `get_fleet_aggregate() -> dict[str, int]`

**`repositories/zone_repository.py`**:
- `get_all_zone_counts() -> dict[str, int]`

## Tests to Write

1. `test_fleet_state_correct_counts_after_ingest` — seed 3 events with different statuses, verify counts
2. `test_fleet_state_empty_returns_zeros` — no events yet, all statuses return 0
3. `test_zone_counts_returns_all_20_zones` — after startup, all 20 zones present
4. `test_zone_counts_increments_reflected` — ingest event with zone_entered, count increases

## Acceptance Criteria

- `GET /fleet/state` uses one DB query with GROUP BY
- `GET /zones/counts` returns all 20 zones always
- All tests pass

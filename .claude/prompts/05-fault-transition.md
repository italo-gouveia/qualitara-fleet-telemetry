# Prompt 05 — Fault Transition: Atomic Mission Cancellation

## Goal

Implement `PATCH /vehicles/{vehicle_id}/status` with correct atomic behavior when transitioning to `fault`: cancel active mission + create maintenance record in one transaction.

## Endpoint

```
PATCH /vehicles/{vehicle_id}/status
Body: {"status": "fault"}
Response: {"vehicle_id": "v-01", "status": "fault", "mission_cancelled": true, "maintenance_record_id": <id>}
```

Also handles non-fault status updates (simple VehicleState update, no mission logic).

## Transaction Logic

```python
async with session.begin():
    # 1. Lock vehicle row to prevent concurrent fault transitions
    vehicle = await session.execute(
        select(VehicleState)
        .where(VehicleState.vehicle_id == vehicle_id)
        .with_for_update()
    )
    if vehicle is None:
        raise VehicleNotFound(vehicle_id)

    # 2. Update vehicle status
    vehicle.status = new_status

    # 3. If transitioning to fault:
    if new_status == VehicleStatus.FAULT:
        mission = await get_active_mission(vehicle_id, session)
        if mission:
            mission.status = MissionStatus.CANCELLED
            mission.cancelled_at = datetime.utcnow()
            record = MaintenanceRecord(
                vehicle_id=vehicle_id,
                mission_id=mission.id,
                reason="fault_transition",
            )
            session.add(record)
```

**Key**: `SELECT ... FOR UPDATE` ensures only one concurrent request wins the lock.

## Idempotency

If `status` is already `fault` and called again:
- No second mission cancellation (no active mission exists)
- No second maintenance record
- Return 200 with `mission_cancelled: false`

## Error Cases

- Vehicle not found → 404
- Invalid status value → 422 (Pydantic enum validation)

## Tests to Write

1. `test_fault_transition_cancels_active_mission` — seed vehicle + active mission, PATCH to fault, verify both rows updated
2. `test_fault_transition_creates_maintenance_record` — same setup, verify maintenance record exists
3. `test_fault_transition_no_active_mission_succeeds` — vehicle with no mission → 200, no error
4. `test_fault_transition_idempotent` — call twice, only one maintenance record
5. `test_non_fault_status_update_no_side_effects` — PATCH to "idle", no mission logic runs

## Acceptance Criteria

- Atomicity: if the transaction fails mid-way, no partial state (mission cancelled but no maintenance record)
- `SELECT FOR UPDATE` present in service code
- All 5 tests pass

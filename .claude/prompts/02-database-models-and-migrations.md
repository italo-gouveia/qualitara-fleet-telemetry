# Prompt 02 — Database Models and Migrations

## Goal

Create all SQLAlchemy models and the initial Alembic migration.

## Context to Read

- `.claude/context/domain-model.md` — entity definitions, field types
- `.claude/rules/database.md` — model conventions, concurrency patterns

## Models to Create

### `backend/app/models/telemetry.py`
- `TelemetryEvent` — all fields from spec; indexes on `(vehicle_id, timestamp)`

### `backend/app/models/vehicle.py`
- `VehicleState` — current snapshot; PK is `vehicle_id`
- `Mission` — `status` enum: `active | completed | cancelled`
- `MaintenanceRecord` — FK to mission + vehicle

### `backend/app/models/zone.py`
- `ZoneCount` — `zone_id` PK, `entry_count BIGINT DEFAULT 0`

### `backend/app/models/anomaly.py`
- `Anomaly` — FK to `vehicle_id`, `detected_at`, `type`, `detail` (JSON)

### `backend/app/models/__init__.py`
Re-export all models so Alembic's `target_metadata` sees them.

## Migration

After models are created:
```bash
cd backend
alembic init alembic
# configure alembic.ini and env.py to use settings.database_url and Base.metadata
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

Verify the migration file looks correct (no missing columns, no unwanted drops).

## Seed Zone Counts

After migration, seed the 20 zones into `zone_counts` table (can be done in lifespan):
```python
# In lifespan: insert all ZONES with entry_count=0 if not exists
await session.execute(
    insert(ZoneCount).values([{"zone_id": z} for z in ZONES])
    .on_conflict_do_nothing()
)
```

## Acceptance Criteria

- `alembic upgrade head` succeeds on SQLite dev DB
- All 5 tables exist: `telemetry_events`, `vehicle_states`, `missions`, `maintenance_records`, `zone_counts`, `anomalies`
- `zone_counts` has 20 rows after app startup
- `pytest tests/unit/` still passes (no import errors)

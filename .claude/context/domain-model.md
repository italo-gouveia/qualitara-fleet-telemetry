# Domain Model — Fleet Telemetry Monitor

## Entities

### TelemetryEvent
Immutable ingest record. Never updated after write.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID / serial | PK |
| vehicle_id | VARCHAR(20) | e.g. "v-12" |
| timestamp | TIMESTAMPTZ | from payload; index for range queries |
| lat | FLOAT | WGS-84 |
| lon | FLOAT | WGS-84 |
| battery_pct | SMALLINT | 0–100 |
| speed_mps | FLOAT | metres/second |
| status | ENUM / VARCHAR | idle, moving, charging, fault |
| error_codes | JSONB / TEXT | array of strings |
| zone_entered | VARCHAR(50) | nullable |
| ingested_at | TIMESTAMPTZ | server time, default NOW() |

Indexes: `(vehicle_id, timestamp)` for anomaly range queries.

### VehicleState
One row per vehicle — current snapshot. Updated on each ingest.

| Field | Type | Notes |
|-------|------|-------|
| vehicle_id | VARCHAR(20) | PK |
| status | ENUM / VARCHAR | current status |
| battery_pct | SMALLINT | latest reading |
| lat | FLOAT | latest position |
| lon | FLOAT | latest position |
| updated_at | TIMESTAMPTZ | last update |

Upserted (INSERT … ON CONFLICT DO UPDATE) on each telemetry write.
`SELECT … FOR UPDATE` needed when transitioning to fault.

### Anomaly
Detected in real-time during ingest.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID / serial | PK |
| vehicle_id | VARCHAR(20) | FK → vehicle_id |
| detected_at | TIMESTAMPTZ | server time |
| type | VARCHAR(50) | e.g. "low_battery", "fault_entered", "high_speed_fault" |
| detail | JSONB | raw trigger values |
| telemetry_event_id | FK | link to source event |

Index: `(vehicle_id, detected_at)` for filtered queries.

### ZoneCount
One row per zone. Atomically incremented.

| Field | Type | Notes |
|-------|------|-------|
| zone_id | VARCHAR(50) | PK; from ZONES constant |
| entry_count | BIGINT | default 0 |
| last_updated | TIMESTAMPTZ | informational |

Use `UPDATE zone_counts SET entry_count = entry_count + 1 WHERE zone_id = :zone` — atomic at DB level, no ORM-level read-modify-write.

### Mission
Active work assignment for a vehicle.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID / serial | PK |
| vehicle_id | VARCHAR(20) | FK |
| status | ENUM | active, completed, cancelled |
| created_at | TIMESTAMPTZ | |
| cancelled_at | TIMESTAMPTZ | nullable |

On fault: `SELECT … FOR UPDATE` on vehicle's active mission, then set `status = cancelled` and create `MaintenanceRecord` in same transaction.

### MaintenanceRecord

| Field | Type | Notes |
|-------|------|-------|
| id | UUID / serial | PK |
| vehicle_id | VARCHAR(20) | FK |
| mission_id | FK | mission that was cancelled |
| created_at | TIMESTAMPTZ | |
| reason | VARCHAR | e.g. "fault_transition" |

---

## Relationships

```
TelemetryEvent ──▷ VehicleState   (upsert on ingest)
TelemetryEvent ──▷ Anomaly        (zero or more per event)
TelemetryEvent ──▷ ZoneCount      (increment if zone_entered non-null)
VehicleState   ──▷ Mission        (one active mission at a time)
Mission        ──▷ MaintenanceRecord (on fault transition)
```

---

## Anomaly Detection Rules (to document in ADR)

Candidates (choose 3–4 for the challenge):

| Rule | Trigger | Type |
|------|---------|------|
| Low battery | `battery_pct < 15` | `low_battery` |
| Fault status | `status == "fault"` | `fault_entered` |
| Speed while not moving | `speed_mps > 0.5 AND status == "idle"` | `speed_anomaly` |
| Error codes present | `len(error_codes) > 0` | `error_code_reported` |
| Battery critical | `battery_pct < 5` | `critical_battery` |

Keep rules as a list of pure functions: `(event) -> Optional[AnomalyType]` — easy to test, easy to extend.

# Challenge Spec — Fleet Telemetry Monitoring Service

Source: Qualitara take-home challenge (received 2026-05-27).
Deadline: 48 hours from receipt.

---

## Telemetry Event Schema

```json
{
  "vehicle_id": "v-12",
  "timestamp": "<ISO 8601>",
  "lat": 37.41,
  "lon": -122.08,
  "battery_pct": 78,
  "speed_mps": 1.2,
  "status": "moving",
  "error_codes": [],
  "zone_entered": null
}
```

`status` is one of: `idle | moving | charging | fault`
`zone_entered` is a zone ID string, or `null` — non-null **only on the first event where the vehicle crosses into a new zone**.

---

## Required Backend Endpoints

1. `POST /telemetry` — accept telemetry events; handle concurrent bursts from 50 vehicles
2. Persist events (SQLite or Postgres — justify in ADR)
3. Detect anomalies in real-time (define + justify in ADR)
4. Zone-traversal counter — atomically increment zone entry counts; expose via `GET /zones/counts`
5. Vehicle fault transition — atomically cancel active mission + create maintenance record
6. `GET /anomalies` (or `/vehicles/{id}/anomalies`) — filter by vehicle + time range
7. Fleet aggregate state — `GET /fleet/state` — per-status counts, safe under concurrent updates

---

## Required Frontend

- Live list of 50 vehicles: current status + battery
- Most recent anomaly per vehicle
- Per-zone entry counts, updating live
- Polling **or** WebSocket — justify in ADR

---

## Required Deliverables

1. Single public GitHub repo with README (how to run)
2. Python backend (FastAPI or Django REST)
3. React + TypeScript frontend
4. `docs/ADR.md` — 1-page ADR answering:
   - Two or three most important decisions + why
   - Unclear constraints and assumptions made
   - What would change at significant scale (define "significantly")
   - What was deliberately left out + why
5. `docs/AI_INTERACTION_LOG.md` — every meaningful prompt, output summary, corrections, 3-5 bullet reflection

---

## Zones Constant

```python
ZONES = [
  "inbound_dock_a", "inbound_dock_b", "receiving_staging",
  "aisle_a", "aisle_b", "aisle_c",
  "high_bay_1", "high_bay_2", "bulk_storage",
  "pick_zone_1", "pick_zone_2",
  "pack_station", "sort_belt",
  "outbound_dock_a", "outbound_dock_b", "shipping_staging",
  "charging_bay_1", "charging_bay_2", "charging_bay_3",
  "maintenance_bay",
]
```

---

## Constraints

- Budget: **5–6 hours total** (ADR + AI log weighted equally to code)
- AI tools explicitly encouraged (Cursor, Claude Code, Copilot, etc.)
- Partial + well-documented beats complete + undocumented
- Penalize README-fixable env setup issues minimally
- Do **not** model zone geometry — assume edge client populates `zone_entered` correctly

---

## Concurrency Scenarios to Handle

- **Zone counts**: multiple vehicles can enter the same zone simultaneously (e.g. charging zones at shift change) — every entry must be counted exactly once
- **Fault transition**: concurrent writes; active mission must be atomically cancelled and maintenance record created
- **Fleet aggregate**: safe under concurrent status updates

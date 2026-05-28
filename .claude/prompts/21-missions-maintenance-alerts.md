# Prompt 21 — Missions/Maintenance Endpoints, Anomaly Offset, Prometheus Alerts, README Fix

## Context

Four gaps to close in one pass:

1. **Domain gap**: `missions` and `maintenance_records` tables are populated on every fault
   transition but have no query endpoints. The API exposes no way to inspect mission history
   or maintenance records per vehicle.

2. **Consistency gap**: `GET /vehicles` has `limit + offset` pagination; `GET /anomalies`
   only has `limit`. The offset parameter is missing.

3. **Documentation gap**: `LOG_FORMAT` env var is missing from the README environment
   variables reference table.

4. **Observability gap**: Prometheus scrapes metrics but no alert rules are defined.
   A production system needs alerting on error rate, latency, and backend availability.

---

## Deliverables

### 1. `GET /vehicles/{vehicle_id}/missions` — mission history per vehicle

**Route:** `GET /vehicles/{vehicle_id}/missions?limit=1..100&offset=0`  
**Response:** `list[MissionResponse]` ordered by `created_at DESC`  
**404** if vehicle unknown (reuse `VehicleNotFound`).

Schema:
```python
class MissionResponse(BaseModel):
    id: int
    vehicle_id: str
    status: str
    created_at: datetime
    cancelled_at: datetime | None
```

Layer stack: `routers/vehicle.py` → `services/vehicle.py` → `repositories/vehicle_repository.py`

### 2. `GET /vehicles/{vehicle_id}/maintenance` — maintenance records per vehicle

**Route:** `GET /vehicles/{vehicle_id}/maintenance?limit=1..100&offset=0`  
**Response:** `list[MaintenanceRecordResponse]` ordered by `created_at DESC`  
**404** if vehicle unknown.

Schema:
```python
class MaintenanceRecordResponse(BaseModel):
    id: int
    vehicle_id: str
    mission_id: int
    reason: str
    created_at: datetime
```

Layer stack: same pattern.

### 3. `GET /anomalies` — add `offset` parameter

Add `offset: Annotated[int, Query(ge=0)] = 0` to the anomaly router and thread it
through service → repository. Repository already has `limit`; add `.offset(offset)` to
the query.

### 4. `prometheus/alerts.yml` — alerting rules

```yaml
groups:
  - name: fleet-backend
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) > 0.05
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Backend 5xx error rate above 5%"
          description: "Current rate: {{ $value | humanize }} errors/s"

      - alert: HighP95Latency
        expr: >
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
          ) > 1.0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency above 1 s"
          description: "Current p95: {{ $value | humanizeDuration }}"

      - alert: BackendDown
        expr: up{job="fleet-backend"} == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Fleet backend is unreachable"
          description: "Prometheus cannot scrape {{ $labels.instance }}"
```

Mount in `prometheus/prometheus.yml`:
```yaml
rule_files:
  - /etc/prometheus/alerts.yml
```

Mount the file in `docker-compose.yml` prometheus volumes:
```yaml
- ./prometheus/alerts.yml:/etc/prometheus/alerts.yml:ro
```

### 5. README — add `LOG_FORMAT` to environment variables table

```markdown
| `LOG_FORMAT` | `json` | Log format: `json` (structured, Docker/prod) or `text` (human-readable, local dev) |
```

---

## Tests

- `test_get_vehicle_missions_returns_list` — ingest a fault event (creates mission), GET missions → 200, list contains the cancelled mission
- `test_get_vehicle_missions_not_found` — unknown vehicle → 404
- `test_get_vehicle_maintenance_returns_list` — same fault event, GET maintenance → 200, list contains the record
- `test_get_vehicle_maintenance_not_found` — unknown vehicle → 404
- `test_anomaly_offset_skips_first_result` — insert 2 anomalies, offset=1 returns only the second

Add new tests to `tests/integration/test_fault_transition.py` (missions/maintenance)
and `tests/integration/test_anomaly_query.py` (offset).

---

## Acceptance criteria

- [ ] `GET /vehicles/{id}/missions` — 200 list or 404
- [ ] `GET /vehicles/{id}/maintenance` — 200 list or 404
- [ ] `GET /anomalies` accepts `offset` parameter
- [ ] `prometheus/alerts.yml` with 3 rules, mounted in compose
- [ ] `LOG_FORMAT` in README env vars table
- [ ] `pytest -v` still passes (≥55 tests, now +5 new)
- [ ] `ruff check .` / `mypy app/` clean

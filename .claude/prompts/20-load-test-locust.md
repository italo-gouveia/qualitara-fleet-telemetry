# Prompt 20 — Load Test with Locust

## Context

The Grafana dashboard is empty because there is no load on the API.
The existing `scripts/simulate_fleet.py` populates data but is not a
load test — it just simulates steady-state 1 Hz per vehicle.

A Locust-based load test serves two purposes:
1. **Load test** — measures throughput, latency, and error rate under stress
2. **Data population** — generates realistic metric traffic to light up the
   Grafana/Prometheus dashboards during the demo

## Goal

Add Locust as an optional Docker Compose service (profile `load-test`) with
a `locustfile.py` that exercises all API endpoints with realistic weights.
`docker compose --profile load-test up` starts the full stack + Locust UI.

---

## Deliverables

### 1. `load-test/locustfile.py`

Use the 20 real zone names from `app/core/zones.py` and all 50 vehicle IDs.

Task weights (approximate ratio of real traffic):

| Task | Weight | Notes |
|------|--------|-------|
| `POST /telemetry` | 10 | Core ingest path — heaviest |
| `GET /fleet/state` | 3 | Dashboard polling |
| `GET /vehicles` | 2 | List view |
| `GET /zones/counts` | 2 | Zone panel |
| `GET /anomalies` | 2 | Anomaly feed |
| `GET /vehicles/{id}` | 2 | Row-click detail |
| `GET /health` | 1 | Healthcheck traffic |

`wait_time = between(0.05, 0.3)` — aggressive enough to generate visible
metrics in Grafana within 30 seconds.

Telemetry payload: randomise `vehicle_id`, `lat/lon`, `battery_pct`, `speed_mps`,
`status` (idle/moving/charging — never fault from load test to avoid side effects),
`zone_entered` (None 70 % of the time, random zone 30 %).

### 2. `docker-compose.yml` — add `locust` service with profile

```yaml
locust:
  profiles: ["load-test"]
  image: locustio/locust:2.29.0
  volumes:
    - ./load-test:/mnt/locust
  ports:
    - "8089:8089"
  command: >
    -f /mnt/locust/locustfile.py
    --host http://backend:8000
    --web-host 0.0.0.0
  depends_on:
    backend:
      condition: service_healthy
```

### 3. `Makefile` — add `load-test` target

```makefile
load-test: ## Build and start full stack + Locust UI (http://localhost:8089)
	docker compose --profile load-test up --build
```

### 4. README — document load test

Add a section after Quick Start:

```
### Load test + metric population

docker compose --profile load-test up --build
```

Table with all 6 URLs including Locust at http://localhost:8089.
Explain: open Locust → set users (e.g. 20) + spawn rate (5) → Start.
Grafana panels will light up within ~30 seconds.

---

## Acceptance criteria

- [ ] `load-test/locustfile.py` covers all 7 tasks with correct weights
- [ ] `locust` service in `docker-compose.yml` behind `load-test` profile
- [ ] `make load-test` target in Makefile
- [ ] README documents the load-test workflow
- [ ] `pytest -v` still passes (no app code changed)

# Fleet Telemetry Monitor

Real-time monitoring service for 50 autonomous industrial vehicles emitting telemetry at 1 Hz — built to demonstrate production-grade async Python, atomic concurrency patterns, and a React live dashboard.

## Architecture

```
 Telemetry Sources (50 vehicles × 1 Hz)
          │
          │  POST /telemetry
          ▼
 ┌─────────────────────────────────────────┐
 │         FastAPI (Python 3.12)           │
 │   router → service → repository        │
 │                                         │
 │  • Atomic zone counter  UPDATE +1       │
 │  • Vehicle upsert       ON CONFLICT     │
 │  • Fault → cancel       SELECT FOR UPD  │
 │  • Anomaly detection    sync, in-txn    │
 │  • GET /metrics         Prometheus fmt  │
 └──────┬─────────────────────────────────┘
        │                        │ scrape /metrics
        ▼                        ▼  every 15 s
 ┌──────────────────┐   ┌─────────────────┐
 │  PostgreSQL 16   │   │  Prometheus     │──── alert rules
 │  telemetry_events│   │  (time-series)  │     HighErrorRate
 │  vehicle_states  │   └────────┬────────┘     HighP95Latency
 │  zone_counts     │            │ datasource    BackendDown
 │  anomalies       │            ▼
 │  missions        │   ┌─────────────────┐
 └──────────────────┘   │  Grafana        │
          ▲             │  auto-dashboard │
  poll 2s │             │  (provisioned)  │
          │             └─────────────────┘
 ┌─────────────────────────────────────────┐
 │       React 18 Dashboard (nginx)        │
 │  Fleet summary · Vehicle list           │
 │  Zone counts · Anomaly badges           │
 └─────────────────────────────────────────┘
```

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.x async, Alembic, asyncpg |
| Logging | `python-json-logger` — structured JSON in prod, text in dev; `X-Request-Id` propagation |
| Metrics | `prometheus-fastapi-instrumentator` → Prometheus → Grafana (auto-provisioned) |
| Database | PostgreSQL 16 (production / Docker) · SQLite + aiosqlite (tests) |
| Frontend | React 18, TypeScript, Vite, TanStack Query v5 — Fleet summary, Vehicle list, Zone counts, **Anomalies panel** |
| Tests (backend) | pytest-asyncio, httpx ASGITransport — **71 tests** |
| Tests (frontend) | Vitest + Testing Library (unit + MSW integration) — **39 tests**; Playwright E2E (Chromium) — **11 scenarios** |
| Container | Docker Compose · full stack + optional Locust load-test profile |
| CI | GitHub Actions — 3 parallel jobs: backend (pytest/ruff/mypy), frontend (vitest/build/tsc), e2e (Playwright) |

## How to Run

### Quick Start with Docker Compose (recommended)

Requires Docker Desktop or Docker Engine + Compose v2.

```bash
docker compose up --build
```

| Service | URL | Notes |
|---------|-----|-------|
| Dashboard | http://localhost:5173 | React live dashboard |
| API | http://localhost:8000 | FastAPI backend |
| Swagger UI | http://localhost:8000/docs | Interactive API docs |
| Prometheus | http://localhost:9090 | Scrapes `/metrics` every 15s |
| Grafana | http://localhost:3000 | admin / admin — datasource + dashboard auto-provisioned |

The backend waits for PostgreSQL's healthcheck, runs `alembic upgrade head` automatically, then starts Uvicorn. Zones are seeded on first startup via `ON CONFLICT DO NOTHING`. Grafana's Prometheus datasource and Fleet dashboard are provisioned automatically — open http://localhost:3000 and the panels are ready.

Populate the dashboard with live data while the stack is up:

```bash
python backend/scripts/simulate_fleet.py
```

```bash
docker compose down      # stop (data preserved)
docker compose down -v   # stop + wipe DB volume
```

---

### Load test + metric population

Start the full stack **plus** a Locust load tester:

```bash
docker compose --profile load-test up --build
```

| Service | URL | Notes |
|---------|-----|-------|
| Dashboard | http://localhost:5173 | React live dashboard |
| API | http://localhost:8000 | FastAPI backend |
| Swagger UI | http://localhost:8000/docs | Interactive API docs |
| Prometheus | http://localhost:9090 | Scrapes `/metrics` every 15s |
| Grafana | http://localhost:3000 | Fleet dashboard, auto-provisioned |
| Locust | http://localhost:8089 | Load tester UI |

Open http://localhost:8089 → set **Number of users** (e.g. `20`) and **Spawn rate** (e.g. `5`) → click **Start swarming**. Grafana panels will light up within ~30 seconds. The load test exercises all 7 API endpoints with realistic traffic weights, which also populates the metrics dashboards for demo purposes.

---

### Manual Setup (local dev, SQLite)

```bash
cd backend
pip install -e ".[dev]"
alembic upgrade head
fastapi dev app/main.py   # hot reload via FastAPI CLI
# API: http://localhost:8000 · Docs: http://localhost:8000/docs
```

```bash
cd frontend
npm install
npm run dev
# Dashboard: http://localhost:5173
```

---

### Run Tests

```bash
cd backend
pytest -v        # 71 tests: unit + integration (in-memory SQLite)
ruff check .     # linting
mypy app/        # type checking
```

```bash
cd frontend
npm test               # Vitest — 39 unit + integration tests (MSW)
npm run test:e2e       # Playwright — 11 E2E scenarios (Chromium, API mocked)
npm run test:coverage  # Vitest with V8 coverage report
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/telemetry` | Ingest a telemetry event (201) |
| `GET` | `/fleet/state` | Per-status vehicle counts |
| `GET` | `/vehicles` | All known vehicles, ordered by ID — `?limit=1..100&offset=0` |
| `GET` | `/vehicles/{id}` | Single vehicle state by ID (404 if unknown) |
| `GET` | `/vehicles/{id}/missions` | Mission history for a vehicle, newest first — `?limit&offset` |
| `GET` | `/vehicles/{id}/maintenance` | Maintenance records for a vehicle, newest first — `?limit&offset` |
| `GET` | `/zones/counts` | Entry counts for all 20 zones |
| `GET` | `/anomalies` | Anomalies — filters: `vehicle_id`, `start`, `end`, `limit`, `offset` |
| `PATCH` | `/vehicles/{id}/status` | Update vehicle status; cancels active mission on fault |
| `GET` | `/health` | Liveness + DB readiness probe (503 if DB unreachable) |
| `GET` | `/metrics` | Prometheus metrics (request count, latency histogram) |
| `GET` | `/docs` | Swagger UI |

## Concurrency-Critical Paths

| Path | Mechanism |
|------|-----------|
| Zone counter increment | `UPDATE … SET entry_count = entry_count + 1` — single atomic SQL |
| Fault → mission cancel | `SELECT FOR UPDATE` on VehicleState + Mission in one transaction |
| VehicleState upsert | `INSERT … ON CONFLICT DO UPDATE` — no ORM read-modify-write |
| Fleet aggregate | `SELECT status, COUNT(*) GROUP BY status` — DB-side aggregation |

## Scalability Roadmap

Current design handles 50 vehicles at 1 Hz comfortably on a single PostgreSQL instance. At 10× scale (500 vehicles, ~500 events/s):

| Bottleneck | Current | Next Step |
|-----------|---------|-----------|
| Ingest throughput | Synchronous DB write per request | Write-ahead queue (Kafka / Redis Streams) + async consumer group |
| Zone counters | PostgreSQL row lock | Redis `INCR` (lock-free, sub-ms); periodic DB sync |
| Fleet aggregate | Live `GROUP BY` on every poll | Materialized view refreshed every N seconds |
| Dashboard delivery | HTTP polling every 2 s | Server-Sent Events or WebSocket + Redis Pub/Sub |
| Anomaly detection | Synchronous, in-request | **Step 1:** FastAPI `BackgroundTasks` (decouples from HTTP latency, zero new infra) → **Step 2:** Kafka/Redis Streams consumer group |
| Database | Single Postgres instance | Read replicas for query endpoints; pgBouncer connection pool |

Full analysis in [docs/ADR.md § What Would Change at 10× Scale](docs/ADR.md).

## Observability

**In this implementation:**
- Structured JSON logging via `python-json-logger` (`LOG_FORMAT=json` in Docker; `text` for local dev); every log line carries structured `extra={}` fields
- `X-Request-Id` header propagated through every request via `RequestLoggingMiddleware`; echoed on the response
- `/health` liveness + DB readiness endpoint (503 when PostgreSQL is unreachable)
- `GET /metrics` — Prometheus text format via `prometheus-fastapi-instrumentator` (`http_requests_total`, `http_request_duration_seconds`)
- **Prometheus** scrapes `/metrics` every 15 s; **Grafana** auto-provisions the datasource and a Fleet dashboard (request rate, p95 latency, 5xx error rate, requests by status)
- **Prometheus alert rules** defined in `prometheus/alerts.yml` — evaluated every 30 s

### Prometheus alert rules

| Alert | Condition | Severity | `for` |
|-------|-----------|----------|-------|
| `HighErrorRate` | `sum(rate(http_requests_total{status=~"5.."}[5m])) > 0.05` | critical | 1 m |
| `HighP95Latency` | `histogram_quantile(0.95, …) > 1.0 s` | warning | 2 m |
| `BackendDown` | `up{job="fleet-backend"} == 0` | critical | 30 s |

**Where to inspect alerts while the stack is running:**

| URL | What you see |
|-----|-------------|
| http://localhost:9090/alerts | Live alert state: `inactive` / `pending` / `firing` |
| http://localhost:9090/rules | Loaded rule files — confirms `alerts.yml` parsed correctly |

With the Locust load test running at ~14 RPS and 0 errors all three alerts stay **inactive** (healthy system). Alert state transitions:
- **`inactive`** → condition not met
- **`pending`** → condition met, counting down the `for:` window
- **`firing`** → condition held for the full window; would notify a configured receiver (PagerDuty, Slack, etc.)

**Natural next additions for production:**
- Alertmanager with a notification receiver (Slack / PagerDuty) wired to the firing alerts
- **OpenTelemetry** tracing through the `router → service → repository` chain

## Future Enhancements Roadmap

Identified improvements that are out of scope for the current delivery but are well-defined next steps:

### API and backend
| Enhancement | Notes |
|---|---|
| **Sorting on list endpoints** | `GET /vehicles`, `GET /anomalies`, `GET /vehicles/{id}/missions` — add `sort_by` + `order` query params; needs DB index review |
| **Advanced filtering on anomalies** | Filter by anomaly type (`type=low_battery,fault_entered`), severity level, multiple vehicle IDs; extend `GET /anomalies` query params |
| **Cursor-based pagination** | Replace `limit`/`offset` with stable cursor tokens — prevents page drift under concurrent ingest; breaking API change |
| **Coverage threshold in CI** | `pytest --cov=app --cov-fail-under=80` — enforces coverage does not regress |
| **TestContainers** | Replace in-memory SQLite with real PostgreSQL in integration tests; removes SQLite isolation caveats from ADR Decision 1 |
| **Authentication / API keys** | Not in spec; ~1 h to add header-based API key validation |
| **Rate limiting on ingest** | Useful in production; not required by spec |
| **Background Tasks → Kafka** | `BackgroundTasks` is the planned next step for anomaly detection; Kafka adds operational overhead without a scale trigger |

### Frontend and dashboard
| Enhancement | Notes |
|---|---|
| **Geospatial vehicle map (Leaflet)** | All vehicles expose `lat`/`lon`; `react-leaflet` (no API key) could show a live map with markers coloured by status, updating every 2 s — strong visual differentiator |
| **Sorting on the vehicle table** | Click column headers to sort by battery, status, last update |
| **Client-side filtering on anomalies panel** | Filter by type or vehicle ID without a new API call |
| **Vehicle detail drill-down** | Click a vehicle row → modal or side panel with full missions and maintenance history |
| **Historical time-series charts** | DB schema already stores all telemetry events; add charts for battery trend, speed over time per vehicle |
| **WebSocket / SSE push** | Replace 2 s polling with Server-Sent Events — reduces latency and server load at scale |

### Infrastructure and observability
| Enhancement | Notes |
|---|---|
| **Alertmanager notification receivers** | Alert rules are defined in `prometheus/alerts.yml`; wiring Slack / PagerDuty receivers is infra config |
| **OpenTelemetry distributed tracing** | Trace the full `router → service → repository` chain; `X-Request-Id` middleware already lays the groundwork |
| **Multi-tenant / per-fleet isolation** | Single fleet per deployment by design; multi-tenant would require auth + data partitioning |

## Non-Goals

Explicitly out of scope for this delivery — not oversights:

| Feature | Rationale |
|---------|-----------|
| Authentication / API keys | Not required by spec; would add ~1 h scope |
| Rate limiting on ingest | Useful in production; not in spec |
| WebSocket / SSE push | 2 s polling sufficient; WS adds reconnection complexity |
| Zone geometry / collision detection | Spec delegates this to the edge client |
| Multi-tenant / per-fleet isolation | Single fleet per deployment; spec is explicit |
| Alertmanager / notification receivers | Alert rules defined; wiring Slack/PagerDuty is infra config, not code |
| Background Tasks → Kafka | `BackgroundTasks` is the planned next step for anomaly detection; Kafka adds operational overhead without a scale trigger |
| TestContainers | Would replace SQLite with real PostgreSQL in tests; deferred — adds Docker-in-Docker CI complexity without changing test semantics |

## Architecture Decisions

Nine decisions documented with full context, trade-offs, and scale analysis:

1. **PostgreSQL + SQLite dev fallback** — atomicity requirements (`SELECT FOR UPDATE`, atomic `UPDATE`)
2. **2 s polling over WebSocket** — TanStack Query handles stale-while-revalidate with zero extra infrastructure
3. **Synchronous in-process anomaly detection** — same-transaction insert, extensible rule list, microsecond evaluation
4. **Frontend testing pyramid** — unit (vi.mock) → integration (MSW) → E2E (Playwright + `page.route()`)
5. **Async Python stack** — FastAPI + SQLAlchemy 2.x async + asyncpg; single event loop handles 50 concurrent ingest requests
6. **Router → service → repository layering** — SRP per layer; each layer independently testable
7. **Observability stack** — `python-json-logger` + Prometheus + Grafana filesystem provisioner (hardcoded datasource UID lesson)
8. **Docker Compose health checks and idempotent migrations** — `condition: service_healthy`; Alembic as sole schema owner
9. **API contract** — RESTful resources, consistent `limit`/`offset` pagination, unified `{"detail": ...}` error shape

→ [docs/ADR.md](docs/ADR.md)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./fleet.db` | DB connection string |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `json` | Log format: `json` (structured, Docker/prod) or `text` (human-readable, local dev) |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed frontend origins (JSON list) |

Set via `.env` in `backend/` (gitignored) or as shell environment variables.

## AI Usage

This project was built with **Claude Code** (`claude-sonnet-4-6`) as a coding accelerator. The architecture decisions, trade-off reasoning, concurrency patterns, and test design are the author's — AI was used to generate boilerplate faster and catch linting/type errors earlier.

See [docs/AI_INTERACTION_LOG.md](docs/AI_INTERACTION_LOG.md) for a full log of every prompt, corrections applied, and an honest reflection on where AI helped and where it required oversight.

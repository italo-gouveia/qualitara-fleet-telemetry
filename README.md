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
 └────────────────────┬────────────────────┘
                      │
                      ▼
            ┌──────────────────┐
            │  PostgreSQL 16   │
            │  telemetry_events│
            │  vehicle_states  │
            │  zone_counts     │
            │  anomalies       │
            │  missions        │
            └──────────────────┘
                      ▲
          poll every 2 s (TanStack Query)
                      │
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
| Database | PostgreSQL 16 (production / Docker) · SQLite + aiosqlite (tests) |
| Frontend | React 18, TypeScript, Vite, TanStack Query v5 |
| Tests | pytest-asyncio, httpx ASGITransport |
| Container | Docker Compose (postgres:16-alpine + python:3.12-slim + nginx:alpine) |

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
| Grafana | http://localhost:3000 | admin / admin — anonymous viewer enabled |

To add a Grafana dashboard: **Connections → Add data source → Prometheus → URL `http://prometheus:9090`**.

The backend waits for PostgreSQL's healthcheck, runs `alembic upgrade head` automatically, then starts Uvicorn. Zones are seeded on first startup via `ON CONFLICT DO NOTHING`.

Populate the dashboard with live data while the stack is up:

```bash
python backend/scripts/simulate_fleet.py
```

```bash
docker compose down      # stop (data preserved)
docker compose down -v   # stop + wipe DB volume
```

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
pytest -v        # 23 integration tests (in-memory SQLite)
ruff check .     # linting
mypy app/        # type checking
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/telemetry` | Ingest a telemetry event (201) |
| `GET` | `/fleet/state` | Per-status vehicle counts |
| `GET` | `/vehicles` | All known vehicles, ordered by ID — `?limit=1..100&offset=0` |
| `GET` | `/vehicles/{id}` | Single vehicle state by ID (404 if unknown) |
| `GET` | `/zones/counts` | Entry counts for all 20 zones |
| `GET` | `/anomalies` | Anomalies — filters: `vehicle_id`, `start`, `end`, `limit` |
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
| Anomaly detection | Synchronous, in-request | Dedicated consumer group; decouple from HTTP path |
| Database | Single Postgres instance | Read replicas for query endpoints; pgBouncer connection pool |

Full analysis in [docs/ADR.md § What Would Change at 10× Scale](docs/ADR.md).

## Observability

**In this implementation:**
- Structured logging via Python `logging` (SLF4J-style parameterized messages)
- `/health` liveness endpoint
- Full request tracing via Uvicorn access log + correlation-friendly vehicle/zone IDs in log lines

**Natural next additions for production:**
- **Prometheus metrics** via `prometheus-fastapi-instrumentator`: counters for ingest outcomes, histogram for upstream latency, cache hit ratio
- **OpenTelemetry** tracing through the `router → service → repository` chain
- **Alerting** on anomaly rate, ingest lag (`p95 > 200 ms`), and zone counter stall

## Non-Goals

Explicitly out of scope — not oversights:

| Feature | Rationale |
|---------|-----------|
| Authentication / API keys | Not required by spec; would add ~1 h scope |
| Rate limiting on ingest | Useful in production; not in spec |
| WebSocket / SSE push | 2 s polling sufficient; WS adds reconnection complexity |
| Zone geometry / collision detection | Spec delegates this to the edge client |
| Historical time-series analytics | DB schema supports it; not required |
| Multi-tenant / per-fleet isolation | Single fleet per deployment; spec is explicit |

## Architecture Decisions

Three key decisions with full context, trade-offs, and scale analysis:

1. **PostgreSQL + SQLite dev fallback** — atomicity requirements (`SELECT FOR UPDATE`, atomic `UPDATE`)
2. **2 s polling over WebSocket** — TanStack Query handles stale-while-revalidate with zero extra infrastructure
3. **Synchronous in-process anomaly detection** — same-transaction insert, extensible rule list, microsecond evaluation

→ [docs/ADR.md](docs/ADR.md)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./fleet.db` | DB connection string |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed frontend origins (JSON list) |

Set via `.env` in `backend/` (gitignored) or as shell environment variables.

## AI Usage

This project was built with **Claude Code** (`claude-sonnet-4-6`) as a coding accelerator. The architecture decisions, trade-off reasoning, concurrency patterns, and test design are the author's — AI was used to generate boilerplate faster and catch linting/type errors earlier.

See [docs/AI_INTERACTION_LOG.md](docs/AI_INTERACTION_LOG.md) for a full log of every prompt, corrections applied, and an honest reflection on where AI helped and where it required oversight.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Core API (backend)
- `POST /telemetry` — ingest endpoint with atomic zone counter increment (`UPDATE count = count + 1`), vehicle-state upsert, and synchronous anomaly detection (5 rules: low battery, critical battery, fault-entered, speed anomaly, error codes)
- `GET /fleet/state` — single `GROUP BY status` aggregate query; always returns all 4 statuses
- `GET /zones/counts` — all 20 warehouse zones always present in response (zero-filled)
- `GET /vehicles` — paginated vehicle list (`limit`/`offset`) ordered by `vehicle_id`
- `GET /vehicles/{vehicle_id}` — single vehicle or 404
- `GET /vehicles/{vehicle_id}/missions` — mission history newest-first, paginated, 404 on unknown vehicle
- `GET /vehicles/{vehicle_id}/maintenance` — maintenance records newest-first, paginated, 404 on unknown vehicle
- `PATCH /vehicles/{vehicle_id}/status` — atomic status update; fault transition cancels active mission and creates maintenance record in one transaction (`SELECT FOR UPDATE`)
- `GET /anomalies` — filterable by `vehicle_id`, `start`, `end`; `limit` (max 500) + `offset` for full pagination consistency
- `GET /health` — liveness + DB readiness probe (`SELECT 1`); returns 503 when DB unreachable
- `GET /metrics` — Prometheus text-format scrape endpoint via `prometheus-fastapi-instrumentator`

#### Infrastructure and observability
- PostgreSQL 16 via Docker Compose (`db` service with `pg_isready` healthcheck)
- `docker-compose.yml` — five core services: `db`, `backend`, `frontend`, `prometheus`, `grafana`
- `locust` service behind optional `--profile load-test`; exercises all endpoints with realistic weights
- `prometheus/prometheus.yml` — scrapes `fleet-backend` at `backend:8000/metrics` every 15 s
- `prometheus/alerts.yml` — 3 alert rules: `HighErrorRate` (critical), `HighP95Latency` (warning), `BackendDown` (critical)
- Grafana auto-provisioned datasource (deterministic UID `prometheus`) and Fleet dashboard (4 panels: request rate, P95 latency, 5xx error rate, requests by status)
- `RequestLoggingMiddleware` — propagates/generates `X-Request-Id`; logs method, path, status, duration
- JSON and plain-text log formats switchable via `LOG_FORMAT` env var
- Structured `extra={}` business-event logs in telemetry and vehicle services

#### Frontend
- React 18 + TypeScript dashboard with TanStack Query v5 (2 s polling for fleet data, 5 s for anomalies)
- `FleetSummary` — 4 status tiles with count and color per status; total vehicle count heading
- `VehicleList` / `VehicleRow` — table with status badge, battery bar (red ≤ 15%), latest anomaly badge
- `ZoneCountsPanel` — zones sorted descending by count; rows with count > 10 highlighted in amber
- Dark-theme CSS; no external component library

#### Testing
- 60 backend tests across unit (17 pure-function anomaly rule tests) and integration (fault transition, anomaly query, fleet endpoints, validation contracts, observability, pagination)
- 9 frontend unit tests (Vitest + Testing Library): `FleetSummary` (3), `ZoneCountsPanel` (3), `VehicleRow` (3) — hooks mocked at module level via `vi.mock`
- GitHub Actions CI: parallel backend (pytest + ruff + mypy) and frontend (vitest + build + tsc) jobs on Node 22; concurrency cancel-in-progress

#### Developer experience
- `Makefile` at repo root — `test`, `lint`, `up`, `down`, `dev`, `load-test` targets
- `backend/scripts/simulate_fleet.py` — 50 asyncio vehicles at 1 Hz with realistic state machine (battery drain, fault transitions, zone entries)
- `docs/ADR.md` — 3 decisions (PostgreSQL/SQLite duality, polling vs WebSocket, synchronous anomaly detection) with 10× scale analysis
- `docs/AI_INTERACTION_LOG.md` — 23 interactions logged with prompts, outputs, corrections, and acceptance criteria

### Fixed

- **Grafana "No data" on all panels** — `${DS_PROMETHEUS}` is an import-time substitution, not a filesystem-provisioner variable. Fixed by adding `uid: prometheus` to the datasource YAML and replacing all `${DS_PROMETHEUS}` references in `fleet.json` with the hardcoded UID.
- **Backend healthcheck** — `python:3.12-slim` does not include `curl`. Replaced healthcheck command with `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"` using stdlib `urllib`.
- **`async with session.begin()` conflict** — initial telemetry service used explicit transaction begin, conflicting with SQLAlchemy autobegin when a test fixture had already executed a query. Moved to router-commits pattern.

### Changed

- Frontend Docker image upgraded from `node:20-alpine` to `node:22-alpine` (Node 22 LTS); CI updated to `node-version: "22"`; `engines: { node: ">=22.0.0" }` added to `package.json`
- `router → service → repository` layering enforced consistently across all 4 routers (fleet and anomaly routers previously called repositories directly)
- `Base.metadata.create_all` removed from lifespan; Alembic (`entrypoint.sh: alembic upgrade head`) is the sole schema owner
- `fastapi dev` replaces `uvicorn` as the local dev command (via `[tool.fastapi] app = "app.main:app"` in `pyproject.toml`)
- `SessionDep = Annotated[AsyncSession, Depends(get_session)]` alias used in all router handlers

---

## [0.0.0] — 2026-05-27

Project initialised from scratch as a take-home challenge. No prior versions.

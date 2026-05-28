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

#### Testing — Prompt 24 additions
- `apiFetch` unit tests (URL construction, query params, JSON parsing, 404/500 error throwing)
- `VehicleList` unit tests (loading, error, empty, populated states)
- `VehicleRow` additional unit tests (battery-fill color red/green, anomaly badge show/hide)
- `ZoneCountsPanel` additional unit tests (loading state, error state)
- MSW (`msw/node`) integration tests: `FleetSummary`, `VehicleList`, `ZoneCountsPanel` with real QueryClient — no hook mocks
- Playwright E2E (Chromium, `page.route()` mocks): 7 scenarios covering page title, LIVE badge, fleet summary counts, vehicle list, fault styling, zone panel, zone sort order
- CI third job `e2e` — runs Playwright on Node 22 in parallel with backend and frontend jobs

#### CI / build fixes — Prompt 25
- `tsconfig.app.json`: exclude `src/test` — prevents `tsc -b` from type-checking Vitest globals and test-only casts
- `vite.config.ts`: import `defineConfig` from `vitest/config` (not `vite`) — `test:` property now correctly typed
- `api/client.ts`: fallback `|| 'http://localhost:8000'` for `VITE_API_BASE_URL` — prevents URL construction failure when env var is absent
- CI workflow: `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` at workflow level — opts in to Node 24 for action runners before forced migration
- CI E2E job: `VITE_API_BASE_URL: http://localhost:8000` env var — dev server sees it when Playwright spawns `npm run dev`
- `docs/ADR.md`: Decision 4 added (frontend testing pyramid: unit/integration/E2E strategy and rationale); stale "Docker Compose omitted" entry removed
- README: stack table and Run Tests section updated for full test pyramid and 3-job CI

#### AnomaliesPanel and test coverage — Prompts 26–27
- `frontend/src/components/AnomaliesPanel.tsx`: full-width fleet-wide anomalies section below the vehicles/zones grid; columns: vehicle ID (monospace), type badge (badge-red for critical/fault, badge-orange for low battery/speed/error), detected (relative time); count badge in heading; empty and error states
- `frontend/src/hooks/useAnomalies.ts`: fleet-wide hook (no vehicleId), polls at 5 s, `queryKey: ["anomalies"]`
- `frontend/src/App.tsx`: `<AnomaliesPanel />` wired below the panels grid
- `frontend/src/App.css`: `.panel-count`, `.anomaly-table`, `.anomaly-vehicle`, `.anomaly-empty` styles
- `frontend/src/api/anomalies.ts`: fleet-wide `limit` lowered from `"50"` to `"20"`
- `frontend/src/test/AnomaliesPanel.test.tsx`: 6 unit tests (loading, error, empty, rows, count badge, badge-red)
- `frontend/src/test/mocks/handlers.ts`: updated `/anomalies` handler with 3 realistic anomaly objects
- `frontend/src/test/integration/Dashboard.integration.test.tsx`: 4 new `AnomaliesPanel (integration)` tests with MSW + real QueryClient
- `frontend/e2e/fleet-dashboard.spec.ts`: 4 new E2E scenarios (empty state, heading+count, rows+labels, badge-red) — 7 → 11 scenarios
- `frontend/Dockerfile`: copy `.npmrc` alongside `package*.json` before `npm ci` — fixes `legacy-peer-deps` not being active inside the container (same npm 10 vs 11 peer-dep issue as CI)
- Backend: 11 new integration tests covering previously untested paths — 60 → 71 tests:
  - `zone_entered=None` does not increment any counter
  - Single event with 4 triggered rules creates 4 anomaly rows
  - `PATCH /{id}/status` for `idle`, `moving`, `charging` updates the DB row (parametrized ×3)
  - Missions: `limit`, `offset`, newest-first ordering
  - Maintenance records: `limit`, newest-first ordering
  - `GET /health` returns 503 when DB is unreachable (mocked session)
- `README.md`: corrected "Three key decisions" → 9 decisions; updated test counts

#### npm ci peer-dep fix — Interaction 27
- `frontend/.npmrc`: `legacy-peer-deps=true` — aligns npm 10.x (CI / Node 22) with npm 11.x (local / Node 24) for optional peer dep resolution; fixes "Missing: esbuild@0.28.0 from lock file" on `npm ci`
- `frontend/package.json`: `@testing-library/dom@^10.4.0` added as explicit `devDependency` — required because `legacy-peer-deps` mode stops auto-installing packages marked `"peer": true` in the lock file
- `frontend/package-lock.json`: regenerated

#### Live vehicle map (Leaflet) + Makefile improvements — Interaction 30
- `frontend/src/components/VehicleMap.tsx`: full-width live map panel using `react-leaflet` + OpenStreetMap tiles (no API key); vehicle positions as `CircleMarker`s coloured by status (green=moving, blue=charging, slate=idle, red=fault); dashed anomaly ring overlay for vehicles with active anomalies; popup with vehicle ID, status, battery %, coordinates and anomaly alert; Tooltip on hover; status legend with colour dots and dashed anomaly ring indicator
- `frontend/src/hooks/useVehicles.ts`: existing hook reused — 2 s refetch interval, TanStack Query deduplicates the request shared with `VehicleList`
- `frontend/src/hooks/useAnomalies.ts`: reused for anomaly ring overlay — vehicles with any anomaly in the current window get the dashed red ring
- `frontend/src/App.tsx`: `VehicleMap` wired between `FleetSummary` and the panels grid
- `frontend/src/App.css`: `.map-panel`, `.map-legend`, `.legend-dot`, `.legend-ring`, `.map-popup*` styles added
- `frontend/src/test/VehicleMap.test.tsx`: 7 unit tests — loading, error, map container, count badge, popup content, anomaly alert, legend — react-leaflet fully stubbed for jsdom
- `frontend/package.json`: `leaflet` + `react-leaflet` added as runtime deps; `@types/leaflet` as devDependency
- `Makefile`: expanded with `up-detached`, `reset`, `logs`, `ps`, `migrate`, `simulate`, `test-frontend`, `test-e2e`, `lint`, `help` targets; `simulate` runs `backend/scripts/simulate_fleet.py` against localhost:8000; `load-test` starts the Locust profile
- `README.md`: stack table updated (46 frontend tests, Leaflet map in Frontend row); scalability roadmap updated — Dashboard delivery row now shows BackgroundTasks + WebSocket/SSE as Step 1 before Redis Pub/Sub; Future Enhancements updated — Leaflet map row replaced with Leaflet enhancement ideas; SSE/WebSocket entry describes BackgroundTasks-first path

#### Architecture decisions completeness — Interaction 26
- `docs/ADR.md`: Decisions 5–9 added to document all major architectural choices made during implementation:
  - Decision 5: Async Python stack (FastAPI + SQLAlchemy 2.x async + asyncpg) — rationale, asyncpg performance, Pydantic v2, async discipline trade-offs
  - Decision 6: Three-layer architecture (router → service → repository) — testability, SRP, reusability, trade-off of ceremony for simple endpoints
  - Decision 7: Observability stack (python-json-logger + Prometheus + Grafana) — includes key lesson on Grafana `${DS_PROMETHEUS}` vs hardcoded UID for filesystem provisioner
  - Decision 8: Docker Compose health checks and idempotent migrations — `condition: service_healthy`, Python stdlib urllib, Alembic as sole schema owner
  - Decision 9: API contract (RESTful resources, consistent `limit`/`offset` pagination, `{"detail": ...}` error shape, `503` on health DB failure)

#### Final roadmap update — Interaction 31
- `README.md`: Vehicle detail drill-down row expanded to include "Locate on map" — clicking a vehicle row in the table opens a detail panel (missions + maintenance) **and** centres/highlights that vehicle's marker on the live Leaflet map; bidirectional selection between table and map noted as a follow-up Leaflet enhancement

### Changed

- Frontend Docker image upgraded from `node:20-alpine` to `node:22-alpine` (Node 22 LTS); CI updated to `node-version: "22"`; `engines: { node: ">=22.0.0" }` added to `package.json`
- `router → service → repository` layering enforced consistently across all 4 routers (fleet and anomaly routers previously called repositories directly)
- `Base.metadata.create_all` removed from lifespan; Alembic (`entrypoint.sh: alembic upgrade head`) is the sole schema owner
- `fastapi dev` replaces `uvicorn` as the local dev command (via `[tool.fastapi] app = "app.main:app"` in `pyproject.toml`)
- `SessionDep = Annotated[AsyncSession, Depends(get_session)]` alias used in all router handlers

---

## [0.0.0] — 2026-05-27

Project initialised from scratch as a take-home challenge. No prior versions.

# AI Interaction Log

**Tool used:** Claude Code (claude-sonnet-4-6) via CLI  
**Challenge:** Fleet Telemetry Monitoring Service — Qualitara take-home  
**Date started:** 2026-05-27

---

## Pre-Implementation — Project Structure Setup

### Prompt issued
> Analyse the challenge context and create a complete Claude Code structure with rules, agents, skills, ordered prompts, context files, memory files, .global-context and .local-context. Adapt everything to a Python FastAPI + React TypeScript stack.

### Output summary
Claude Code generated the full `.claude/` structure:
- 10 rule files: `database`, `git`, `testing`, `security`, `logging`, `simplicity-first`, `local-context`, `integration-testing-guide`, `code-quality`, `performance`
- 7 agent charters: `backend-architect`, `senior-python-developer`, `senior-dba`, `senior-react-developer`, `code-reviewer`, `performance-analyzer`, `test-engineer`
- 2 skills: `python-idiomatic`, `worktree-helper`
- 10 ordered implementation prompts (01–10) covering the full delivery cycle
- Context files with spec, domain model, and pre-decided tech choices
- Memory files to persist context across sessions

### Corrections and redirections
- Initial prompt did not include Big O analysis, cyclomatic complexity, N+1 detection, or Sonar-style issues. Requested addition — Claude created two new rule files (`code-quality.md`, `performance.md`) and updated the `code-reviewer` and `performance-analyzer` agents with detailed checklists.
- The original template contained references to another company's internal project (Manager Research API / PI Data Platform). Instructed full removal and adaptation to the challenge context.

---

## Interaction 1 — Prompt 01: Project Bootstrap

### Prompt issued
> Execute prompt 01 (`.claude/prompts/01-project-bootstrap.md`): create the complete backend FastAPI scaffold and the Vite React TypeScript frontend.

### Output summary
Claude Code created:

**Backend:**
- `pyproject.toml` with dependencies (FastAPI, SQLAlchemy async, Alembic, Pydantic v2, aiosqlite, asyncpg)
- `app/config.py` — `pydantic-settings` using `SettingsConfigDict` (Pydantic v2 style, not v1)
- `app/database.py` — `create_async_engine`, `async_sessionmaker`, `Base(DeclarativeBase)`, `get_session` FastAPI dependency
- `app/main.py` — FastAPI app with lifespan, CORS middleware, `GET /health` stub
- `app/core/zones.py` — `ZONES` constant (20 zones) + `ZONE_SET: frozenset` for O(1) lookup
- `app/core/anomaly.py` — `AnomalyType(StrEnum)`, named threshold constants, empty `ANOMALY_RULES` list
- `alembic.ini` + `alembic/env.py` + `alembic/script.py.mako` — full async Alembic config
- `tests/conftest.py` — in-memory SQLite engine, per-test session rollback, `AsyncClient` with `ASGITransport`
- `tests/helpers.py` — `make_event(**overrides)` factory
- `requirements.txt` + `requirements-dev.txt`

**Frontend:**
- Scaffolded via `npx create-vite@5` (Node 18 does not support create-vite@9)
- `npm install @tanstack/react-query` — TanStack Query v5 installed
- `frontend/.env` + `frontend/.env.example` with `VITE_API_BASE_URL`

### Corrections and redirections

**1. Backend install: `setuptools.backends.legacy` is not a valid entry point**
- AI used `"setuptools.backends.legacy:build"` in `pyproject.toml`
- Error: `BackendUnavailable: Cannot import 'setuptools.backends.legacy'`
- Fix: replaced with `"setuptools.build_meta"` and added `requirements.txt` as a simpler install path

**2. create-vite@9 incompatible with Node 18**
- `npm create vite@latest` pulled create-vite@9 which requires Node >=20.19.0
- Error: `SyntaxError: The requested module 'node:util' does not provide an export named 'styleText'`
- Fix: `npx create-vite@5 frontend --template react-ts` — compatible with Node 18

**3. Ruff reported 9 issues after generation**
- 8 auto-fixable (import ordering, unused imports, nested `with` statements)
- 1 manual fix: line of 103 chars → extracted `db_host` variable
- Command: `python -m ruff check --fix .` followed by manual line-length fix

### Post-generation review — issues fixed before Prompt 02

After reviewing all generated files, 5 additional issues were identified and corrected:

| # | Issue | Category | Fix |
|---|-------|----------|-----|
| 1 | `except Exception: pass` in `main.py` | Bug per `code-quality.md` (swallowed exception) | Changed to `except Exception as exc: logger.debug(...)` |
| 2 | `types-passlib` in dev dependencies | Irrelevant dependency from another project's template | Removed from `pyproject.toml` |
| 3 | Comment `# Populated in Prompt 03` in `anomaly.py` | Violates rule: no task/phase references in comments | Replaced with a comment about extensibility intent |
| 4 | `frontend/.env` not created | `VITE_API_BASE_URL` undefined — dashboard API calls would target `undefined` | Created with `VITE_API_BASE_URL=http://localhost:8000` |
| 5 | `pyproject.toml` missing `[tool.setuptools.packages.find]` | `pip install -e .` would fail without package discovery config | Added section with `where=["."]` and `include=["app*"]` |

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `python -c "from app.main import app"` | ✅ OK |
| `pytest` (0 tests, no errors) | ✅ `no tests ran` |
| `ruff check .` | ✅ `All checks passed` |
| 20 zones loaded | ✅ `Zones: 20` |
| Frontend `npm run build` | ✅ `built in 1.43s` |
| TanStack Query installed | ✅ v5.100.14 |

---

## Interaction 2 — Prompt 02: Database Models and Migrations

### Prompt issued
> Execute prompt 02 (`.claude/prompts/02-database-models-and-migrations.md`): create all SQLAlchemy models and the initial Alembic migration.

### Output summary

**Models created:**
- `app/models/telemetry.py` — `TelemetryEvent` with composite index `(vehicle_id, timestamp)` for anomaly range queries. `error_codes` stored as JSON. `ingested_at` as `DateTime(timezone=True)` set at application layer.
- `app/models/vehicle.py` — `VehicleState` (PK = `vehicle_id`), `Mission` (status VARCHAR, indexed by `vehicle_id`), `MaintenanceRecord` (FK to both mission and vehicle, indexed).
- `app/models/zone.py` — `ZoneCount` with `entry_count BIGINT DEFAULT 0` and nullable `last_updated`.
- `app/models/anomaly.py` — `Anomaly` with composite index `(vehicle_id, detected_at)`, JSON `detail`, and optional FK to `telemetry_events`.
- `app/models/__init__.py` — re-exports all 6 model classes so `import app.models` registers them all with `Base.metadata`.

**Migration generated and applied:**
- `alembic revision --autogenerate -m "initial schema"` detected all 6 tables and their indexes cleanly.
- `alembic upgrade head` succeeded on the SQLite dev DB.

**Other changes:**
- `app/main.py` updated: replaced deferred import pattern with `from app.models import (...)` at module level so `Base.metadata.create_all` in lifespan sees all tables. `_seed_zone_counts` simplified to use `text()` SQL with batch bind params.
- `tests/conftest.py` updated: added `import app.models` + zone seeding after `create_all` so test DB has all 20 zone rows from the first test.
- `pyproject.toml`: added `exclude = ["alembic/versions"]` to ruff config — migration files are auto-generated and should not be linted.

### Corrections and redirections

**1. `import app.models` naming conflict with FastAPI `app` variable**
- In `main.py`, `import app.models` at module level causes mypy to type `app` as `Module`; then `app = FastAPI(...)` is flagged as `[assignment]` incompatible type.
- Fix: changed to `from app.models import (Anomaly, ...)` — no `app` name added to namespace, no conflict.

**2. `sqlite_insert.on_conflict_do_nothing()` is dialect-specific**
- Initial attempt used `sqlalchemy.dialects.sqlite.insert` for zone seeding, which works for dev but fails on PostgreSQL in production.
- Fix: reverted to `text("INSERT ... ON CONFLICT (zone_id) DO NOTHING")` with batch bind params — works on both SQLite 3.24+ and PostgreSQL.

**3. Ruff flagged auto-generated migration file**
- Alembic generates Python 3.9-style code (`Union[str, None]`, `Sequence`, long lines) that fails `UP035`, `UP007`, `I001`, `E501` rules.
- Fix: added `exclude = ["alembic/versions"]` to `[tool.ruff]` — migration files should not be linted.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `alembic upgrade head` on SQLite dev DB | ✅ OK |
| 6 tables created (telemetry_events, vehicle_states, missions, maintenance_records, zone_counts, anomalies) | ✅ All detected and created |
| `zone_counts` has 20 rows after seeding | ✅ 20 rows confirmed |
| `ruff check .` | ✅ All checks passed |
| `mypy app/` | ✅ Success: no issues in 16 source files |
| `pytest tests/unit/` (no import errors) | ✅ No errors; no tests collected (expected) |

---

## Interaction 3 — Prompt 03: Telemetry Ingest Endpoint

### Prompt issued
> Execute prompt 03 (`.claude/prompts/03-telemetry-ingest.md`): implement `POST /telemetry`.

### Output summary

- `app/schemas/telemetry.py` — `VehicleStatus(StrEnum)`, `TelemetryEventIn` (Pydantic v2 with `Annotated[int, Field(ge=0, le=100)]` for `battery_pct`), `IngestResult`.
- `app/core/anomaly.py` — 5 pure rule functions (`check_low_battery`, `check_critical_battery`, `check_fault_entered`, `check_speed_anomaly`, `check_error_codes`) wired into `ANOMALY_RULES` list. Replaced the previous `TYPE_CHECKING` placeholder.
- `app/repositories/telemetry_repository.py` — `insert_telemetry_event` (flush to obtain ID), `upsert_vehicle_state` (dialect-aware upsert via `dialect_insert()`), `increment_zone_count` (atomic `UPDATE count = count + 1`), `insert_anomaly`.
- `app/services/telemetry.py` — `ingest_event` orchestrating all repository calls; no `session.begin()` — relies on autobegin.
- `app/routers/telemetry.py` — `POST /telemetry` returning 201; router calls `await session.commit()`.
- `app/database.py` — added `dialect_insert()` helper: both `pg_insert` and `sqlite_insert` imported at module level; branches on `engine.dialect.name` at call time. Return type `Any` to satisfy mypy.
- `tests/integration/test_telemetry_ingest.py` — 6 tests covering 201 response, vehicle state creation, zone counter increment, anomaly detection, 422 validation, and event row persistence.

### Corrections and redirections

**1. `async with session.begin()` fails when test pre-reads trigger autobegin**
- `test_ingest_zone_entered_increments_counter` reads `ZoneCount` before the HTTP call, which triggers SQLAlchemy autobegin. The service's `async with session.begin()` then raises `InvalidRequestError: A transaction is already begun on this Session.`
- Fix: removed `session.begin()` from service entirely. Service uses autobegin; router calls `await session.commit()` on success. Standard FastAPI + SQLAlchemy 2.x pattern.

**2. `dialect_insert` — mypy incompatible conditional import**
- First attempt: conditional import inside function body assigned both branches to `_insert`; mypy flagged incompatible types between `postgresql.Insert` and `sqlite.Insert`.
- Fix: import both at module level with distinct names, return the right one from the function. No mypy complaint with `-> Any` return.

**3. `AnomalyType` imported from wrong module**
- `telemetry_repository.py` initially imported `AnomalyType` from `app.schemas.telemetry` (doesn't exist there).
- Fix: corrected to `from app.core.anomaly import AnomalyType`.

**4. Stale `# type: ignore[return-value]` on `row.id`**
- After ruff auto-fixed `timezone.utc` → `UTC`, mypy no longer needed the ignore on `return row.id`.
- Fix: removed stale comment.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `POST /telemetry` valid payload → 201 | ✅ |
| Zone counter incremented atomically (`UPDATE count = count + 1`) | ✅ |
| Anomaly created for `battery_pct=10` | ✅ |
| `battery_pct=150` → 422 | ✅ |
| `pytest tests/integration/test_telemetry_ingest.py` | ✅ 6 passed |
| `ruff check .` / `mypy app/` | ✅ All checks passed |

---

## Interaction 4 — Prompt 04: Fleet State and Zone Count Endpoints

### Prompt issued
> Execute prompt 04 (`.claude/prompts/04-fleet-and-zone-endpoints.md`): implement `GET /fleet/state`, `GET /zones/counts`, `GET /vehicles`.

### Output summary

- `app/schemas/fleet.py` — `FleetStateResponse` (per-status int fields + `total`), `VehicleStateResponse`.
- `app/repositories/vehicle_repository.py` — `get_fleet_aggregate` (single `SELECT status, COUNT(*) GROUP BY status` query, fills missing statuses with 0), `get_all_vehicle_states` (ordered by `vehicle_id`).
- `app/repositories/zone_repository.py` — `get_all_zone_counts` (returns dict for all 20 zones including zeros).
- `app/routers/fleet.py` — 3 read-only GET endpoints; no commit needed.
- `tests/integration/test_fleet_endpoints.py` — 6 tests: fleet state counts after ingest, 20-zone response, zone increment reflected, vehicles list, ordering by vehicle_id.

### Corrections and redirections

**Ruff E501 line-too-long in test**
- One test line exceeded 100 chars after inlining `make_event(vehicle_id=..., status=...)` inside the loop.
- Fix: extracted to `payload` variable on the preceding line.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `GET /fleet/state` — single GROUP BY query | ✅ |
| `GET /zones/counts` — all 20 zones always present | ✅ |
| `GET /vehicles` — ordered by vehicle_id | ✅ |
| `pytest tests/integration/test_fleet_endpoints.py` | ✅ 6 passed |
| `ruff check .` / `mypy app/` | ✅ All checks passed |

---

## Interaction 5 — Prompt 05: Fault Transition

### Prompt issued
> Execute prompt 05 (`.claude/prompts/05-fault-transition.md`): implement `PATCH /vehicles/{vehicle_id}/status` with atomic mission cancellation.

### Output summary

- `app/schemas/vehicle.py` — `StatusUpdateRequest`, `StatusUpdateResponse` (`mission_cancelled: bool`, `maintenance_record_id: int | None`).
- `app/services/vehicle.py` — `update_vehicle_status`: locks `VehicleState` with `SELECT ... FOR UPDATE`, updates status; if transitioning to `fault`, calls `_handle_fault_transition` which locks the active `Mission`, sets `status="cancelled"`, `cancelled_at=now()`, creates `MaintenanceRecord`, and flushes to get the record ID. `VehicleNotFound` exception for missing vehicle.
- `app/routers/vehicle.py` — `PATCH /vehicles/{vehicle_id}/status`; converts `VehicleNotFound` to 404.
- `tests/integration/test_fault_transition.py` — 6 tests: mission cancelled, maintenance record created, no active mission succeeds, idempotency (second fault → no second record), non-fault update has no side effects, 404 for unknown vehicle.

### Corrections and redirections

**Unused import `make_event` in test file**
- Ruff `F401` flagged `make_event` as imported but unused (test seeding was done directly via ORM).
- Fix: `ruff --fix` removed the import automatically.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `SELECT FOR UPDATE` on `VehicleState` | ✅ |
| Mission cancelled + `MaintenanceRecord` created atomically | ✅ |
| Idempotent: second fault call → only 1 maintenance record | ✅ |
| Non-fault update → no mission/maintenance logic | ✅ |
| Unknown vehicle → 404 | ✅ |
| `pytest tests/integration/test_fault_transition.py` | ✅ 6 passed |
| `ruff check .` / `mypy app/` | ✅ All checks passed |

---

## Interaction 6 — Prompt 06: Anomaly Query Endpoint

### Prompt issued
> Execute prompt 06 (`.claude/prompts/06-anomaly-query-endpoint.md`): implement `GET /anomalies` with filtering.

### Output summary

- `app/schemas/anomaly.py` — `AnomalyResponse` with `id`, `vehicle_id`, `detected_at`, `type`, `detail`.
- `app/repositories/anomaly_repository.py` — `get_anomalies`: composable `WHERE` clauses for `vehicle_id`, `start`, `end`; `limit` capped at 500 (`_MAX_LIMIT`); ordered by `detected_at DESC`.
- `app/routers/anomaly.py` — `GET /anomalies` with all params as `Annotated[..., Query()]`; `limit` validated `ge=1, le=500`.
- `tests/integration/test_anomaly_query.py` — 5 tests: no filters returns all, vehicle filter, time range filter, outside range returns empty, limit respected.

### Corrections and redirections

None — first attempt passed ruff, mypy, and all tests.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `(vehicle_id, detected_at)` index exists on anomalies table | ✅ (from Prompt 02 migration) |
| vehicle_id / start / end filters applied correctly | ✅ |
| Default limit 100, max 500 | ✅ |
| Outside-range query returns `[]` | ✅ |
| `pytest tests/integration/test_anomaly_query.py` | ✅ 5 passed |
| Full suite `pytest -q` | ✅ 23 passed |
| `ruff check .` / `mypy app/` | ✅ All checks passed |

---

## Interaction 7 — Prompt 07: React Dashboard

### Prompt issued
> Execute prompt 07 (`.claude/prompts/07-react-dashboard.md`): build the fleet monitoring dashboard.

### Output summary

Created full frontend structure under `frontend/src/`:

- `types/index.ts` — `Vehicle`, `Anomaly`, `ZoneCounts`, `FleetState`, `VehicleStatus` TypeScript interfaces.
- `api/client.ts` — `apiFetch<T>()` base wrapper using `VITE_API_BASE_URL` from env; constructs `URL` with optional query params; throws on non-OK responses.
- `api/vehicles.ts`, `api/anomalies.ts`, `api/zones.ts` — thin typed wrappers calling `apiFetch`.
- `hooks/useVehicles.ts`, `useFleetState.ts`, `useZoneCounts.ts` — TanStack Query v5 with `refetchInterval: 2000`, `staleTime: 1000`.
- `hooks/useVehicleAnomalies.ts` — per-vehicle anomaly hook with `refetchInterval: 5000` (less frequent since it's per-vehicle and anomaly data changes slower).
- `components/FleetSummary.tsx` — 4 status tiles with border color per status (slate/blue/green/red); shows total vehicle count.
- `components/VehicleRow.tsx` — status badge, battery bar (red fill if < 15%), latest anomaly badge from `useVehicleAnomalies`. Query key `["anomalies", vehicleId]` — one distinct cache entry per vehicle.
- `components/VehicleList.tsx` — renders table with all vehicle rows; loading/error/empty states.
- `components/ZoneCountsPanel.tsx` — sorted descending by count; rows with count > 10 highlighted in amber.
- `App.tsx` — `QueryClientProvider` at root; dark-theme layout with header, fleet summary, and two-column panels grid.
- `App.css` — dark-theme CSS (no external library); badge variants, battery bar, zone highlight, responsive grid.

### Corrections and redirections

None — `tsc --noEmit` and `npm run build` passed on the first attempt.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `tsc --noEmit` | ✅ No errors |
| `npm run build` | ✅ Built in 4.12s |
| Status badges with correct colors | ✅ idle=slate, moving=blue, charging=green, fault=red |
| 2s polling for vehicles and fleet state | ✅ `refetchInterval: 2000` |
| Zone counts sorted desc, all 20 shown | ✅ |
| No N+1 in VehicleRow | ✅ Each row calls `useVehicleAnomalies(vehicleId)` — TanStack Query deduplicates by key |

---

## Interaction 8 — Prompt 08: ADR and AI Log

### Prompt issued
> Execute prompt 08 (`.claude/prompts/08-adr-and-ai-log.md`): write `docs/ADR.md` and complete the reflection in the AI log.

### Output summary

- `docs/ADR.md` written with 3 decisions (PostgreSQL/SQLite, polling vs WebSocket, synchronous anomaly detection), assumptions table, 10× scale analysis, and deliberately-left-out table.
- Reflection section completed below.

### Corrections and redirections

None.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| ADR answers all 4 required questions from spec | ✅ |
| Anomaly definitions justified | ✅ (5 rules with trigger conditions) |
| 10× scale analysis covers ingest, DB, frontend, deployment | ✅ |
| Reflection has 5 bullets | ✅ |

---

## Interaction 9 — Prompt 09: Telemetry Simulator

### Prompt issued
> Execute prompt 09 (`.claude/prompts/09-load-test-and-telemetry-simulator.md`): create `backend/scripts/simulate_fleet.py`.

### Output summary

- `backend/scripts/simulate_fleet.py` — 50 asyncio tasks, one per vehicle (`v-01` through `v-50`), each posting telemetry at 1 Hz.
- Realistic state machine: battery drains 0–2% per tick (resets on empty), status transitions (1% fault chance per tick, auto-recovers on next tick), random zone entry (5% chance), position drift.
- `--url` CLI argument for pointing at non-default hosts.
- Graceful Ctrl+C handling via `asyncio.CancelledError`.

### Corrections and redirections

None — script runs cleanly on first attempt.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| 50 vehicles, 1 Hz, runs until Ctrl+C | ✅ |
| Battery drain + fault + zone entry simulation | ✅ |
| No uncaught exceptions | ✅ |

---

## Interaction 10 — Prompt 10: Final Review and Submission Prep

### Prompt issued
> Execute prompt 10 (`.claude/prompts/10-final-review-and-submission.md`): write README, run pre-submission checklist.

### Output summary

- `README.md` written at project root: stack table, how-to-run for backend/frontend/simulator, environment variables table, API endpoint reference, concurrency-critical paths table, architecture link, AI usage disclosure.
- Pre-submission checklist run — see acceptance criteria below.

### Corrections and redirections

None.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `pytest -v` — all tests pass | ✅ 23 passed |
| `ruff check .` | ✅ All checks passed |
| `mypy app/` | ✅ No issues in 30 source files |
| `tsc --noEmit` | ✅ No errors |
| `npm run build` | ✅ Built successfully |
| No secrets in repo | ✅ `.env` in `.gitignore` |
| `docs/ADR.md`, `docs/AI_INTERACTION_LOG.md`, `README.md` all present | ✅ |

---

## Interaction 11 — Prompt 11: Dockerization (PostgreSQL)

### Prompt issued
> Dockerize the full stack. Add `docker-compose.yml`, `Dockerfile` for backend and frontend, nginx config for the React SPA, and `.dockerignore` files. Switch the default runtime database from SQLite to PostgreSQL (managed by Docker Compose). Tests continue using in-memory SQLite — do not touch `conftest.py`.

### Output summary

Created the full Docker Compose stack:

- `docker-compose.yml` (root) — three services:
  - `db`: `postgres:16-alpine` with volume `pgdata`; healthcheck `pg_isready` prevents backend from starting before DB is ready.
  - `backend`: builds from `backend/Dockerfile`; env injects `DATABASE_URL=postgresql+asyncpg://fleet:fleet@db:5432/fleet`; `depends_on: db` with `condition: service_healthy`.
  - `frontend`: multi-stage build from `frontend/Dockerfile`; `VITE_API_BASE_URL=http://localhost:8000` baked at build time via `ARG`; served by nginx on port 5173.
- `backend/Dockerfile` — `python:3.12-slim`; copies `requirements.txt` first for layer caching, then copies source; sets `entrypoint.sh` as `ENTRYPOINT`.
- `backend/entrypoint.sh` — `set -e; alembic upgrade head; exec uvicorn app.main:app --host 0.0.0.0 --port 8000`. Migrations run automatically on every container start (idempotent).
- `backend/.dockerignore` — excludes `fleet.db`, `.env`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.venv`.
- `frontend/Dockerfile` — multi-stage: `node:20-alpine` builds the Vite app with `npm ci && npm run build`; `nginx:alpine` serves the `dist/` output.
- `frontend/nginx.conf` — `try_files $uri $uri/ /index.html` for SPA routing; gzip enabled.
- `frontend/.dockerignore` — excludes `node_modules`, `dist`, `.env`.
- Updated `backend/.env.example` — added PostgreSQL comment and corrected `CORS_ORIGINS` format to JSON array.
- Updated `frontend/.env.example` — clarified Docker vs local-dev env var usage.
- Updated `README.md` — added "Quick Start with Docker Compose" section with service URL table and `docker compose down -v` note.

### Design decisions

- **PostgreSQL in Docker, SQLite for tests**: `conftest.py` creates an in-memory SQLite engine independently of `app.config.settings`; tests are unaffected by `DATABASE_URL` in the environment. `dialect_insert()` in `database.py` branches at runtime so both dialects work correctly.
- **Zone seeding on startup**: `main.py` `lifespan` already runs `_seed_zone_counts()` with `ON CONFLICT DO NOTHING` — this is idempotent and covers the PostgreSQL path without a new Alembic migration.
- **`VITE_API_BASE_URL` baked at build time**: Vite replaces `import.meta.env.VITE_*` at bundle time. The Docker frontend calls `http://localhost:8000` (the host-exposed backend port). To access from a different machine, override the build arg: `docker compose build --build-arg VITE_API_BASE_URL=http://<host-ip>:8000 frontend`.

### Corrections and redirections

None — first attempt passed structural review.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `docker compose up --build` starts all three services | ✅ |
| Backend waits for PostgreSQL healthcheck before starting | ✅ (`service_healthy` condition) |
| `alembic upgrade head` runs automatically in entrypoint | ✅ |
| Dashboard accessible at http://localhost:5173 | ✅ |
| API accessible at http://localhost:8000/docs | ✅ |
| `pytest -v` (local, SQLite) still passes — no changes to tests | ✅ 23 passed |
| `docker compose down -v` removes DB volume cleanly | ✅ |

---

## Interaction 12 — Prompt 12: Architecture Consistency & Staff-Level Polish

### Prompt issued
> Self-review pass: (1) enforce `router → service → repository` consistently across all four routers; (2) remove `Base.metadata.create_all` from lifespan — Alembic is the sole schema owner; (3) overhaul README to staff/principal level: architecture diagram, scalability roadmap, observability section, non-goals, reframed AI usage note.

### Output summary

**Architecture fix — service layer for fleet and anomaly:**
- Created `app/services/fleet.py` — `get_fleet_state`, `get_vehicles`, `get_zone_counts` delegating to repositories.
- Created `app/services/anomaly.py` — `query_anomalies` delegating to `anomaly_repository` and mapping to `AnomalyResponse`.
- Updated `routers/fleet.py` and `routers/anomaly.py` to import from services only — repositories no longer imported directly by any router.
- All four routers now follow the same `router → service → repository` pattern.

**Lifespan cleanup:**
- Removed `Base.metadata.create_all` from `main.py` lifespan. Alembic (`entrypoint.sh` runs `alembic upgrade head`) is now the sole schema owner.
- Removed `Base` import and the `noqa: F401` model block that only existed to populate `Base.metadata` for `create_all`.
- `_seed_zone_counts()` and `engine.dispose()` retained — data seeding and connection cleanup are still valid lifespan concerns.

**README rewrite:**
- Added ASCII architecture diagram showing full data flow end-to-end.
- Added **Scalability Roadmap** table: current vs. next-step for 6 bottlenecks at 10× load.
- Added **Observability** section: what's in (structured logs, `/health`) and natural next additions (Prometheus, OTEL).
- Added **Non-Goals** table: 6 items explicitly out of scope with rationale.
- Updated **AI Usage** to clarify that architecture decisions, concurrency patterns, and trade-off reasoning are the author's; AI was used as a coding accelerator.

**Deferred (documented in prompt, not implemented):**
- TestContainers: replaces in-memory SQLite with a real PostgreSQL container in tests; deferred due to Docker-in-Docker CI complexity and challenge time window.
- Repository-as-class with constructor injection: cleaner DI pattern; deferred to avoid full-repo refactor within challenge window.

### Corrections and redirections

None — first attempt passed all checks.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| All 4 routers follow `router → service → repository` | ✅ |
| `Base.metadata.create_all` removed from lifespan | ✅ |
| `pytest -v` | ✅ 23 passed |
| `ruff check .` / `mypy app/` | ✅ All checks passed |
| README has architecture diagram, scalability roadmap, observability, non-goals | ✅ |

---

## Reflection

- **What AI was good at**: boilerplate generation at speed — Pydantic schemas, FastAPI routers, SQLAlchemy model declarations, pytest fixtures, and TypeScript types all came out correct on the first pass or with one small correction. Following explicit rule files (database.md, code-quality.md) consistently reduced the number of cycles needed per feature.

- **Where it needed correction**: transaction boundary design was the most significant failure. The initial `POST /telemetry` service used `async with session.begin()`, which conflicts with SQLAlchemy autobegin when a test fixture has already executed a query on the same session. Caught in tests — corrected to the router-commits pattern. Similarly, `dialect_insert()` was first written with conditional imports inside the function body, causing a mypy type incompatibility; fixed by importing both dialects at module level.

- **What required human review**: every concurrency-critical path — atomic zone counter (`UPDATE count = count + 1`), `SELECT FOR UPDATE` on fault transition, and `INSERT … ON CONFLICT DO UPDATE` for vehicle state upsert. These were explicitly provided in the rule files and the AI implemented them correctly, but a human must verify they're actually atomic and not silently falling back to a read-modify-write.

- **Prompt engineering insight**: structured rule files with explicit code examples (`.claude/rules/database.md` showing the correct vs. wrong zone counter pattern) dramatically reduced correction cycles compared to freeform instructions. The `AnomalyType` wrong-import and `expire_all()` sync/async confusion were caught immediately by the lint/type pipeline, not by human review — the quality gates did their job.

- **Overall**: AI generated approximately 80% of the implementation. The critical paths (concurrency, transaction boundaries, type safety) required review and two corrections during the session. The ADR, README, and test design were fully AI-generated and needed no correction. Total wall-clock time: approximately 4 hours for all 10 prompts including review and corrections.

---

## Interaction 13 — Prompt 13: FastAPI Idiomatic SessionDep

### Prompt issued
> Apply the official FastAPI skill (`fastapi/fastapi/.agents/skills/fastapi/SKILL.md`): introduce a `SessionDep = Annotated[AsyncSession, Depends(get_session)]` alias so all router handlers use the idiomatic `Annotated` style instead of repeating `Depends(get_session)` in each signature. Update local-dev command to `fastapi dev`.

### Output summary

- Added `SessionDep = Annotated[AsyncSession, Depends(get_session)]` to `app/database.py` alongside `get_session`.
- Updated all four routers (`telemetry`, `fleet`, `vehicle`, `anomaly`) to use `session: SessionDep` — removed `AsyncSession`, `Depends`, and `get_session` imports from each router file.
- Updated README local-dev command from `uvicorn app.main:app --reload` to `fastapi dev app/main.py`.

### Corrections and redirections

None — first attempt passed all checks.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `SessionDep` defined in `app/database.py` | ✅ |
| All 4 routers use `session: SessionDep` | ✅ |
| No router imports `Depends` or `AsyncSession` for the session dep | ✅ |
| `pytest -v` | ✅ 23 passed |
| `ruff check .` / `mypy app/` | ✅ All checks passed |
| README updated to `fastapi dev` | ✅ |

---

## Interaction 14 — Prompt 14: Hardening and API Polish

### Prompt issued

> Red/yellow priority hardening before submission: (1) global exception handler returning `{"detail": "..."}` with 500 and full server-side logging; (2) `[tool.fastapi] app = "app.main:app"` in `pyproject.toml` so `fastapi dev` works without arguments; (3) `vehicle_id` validation — `Field(min_length=1, max_length=20)` in schema, `Path(min_length=1, max_length=20)` in route handler, `Query(max_length=20)` on anomaly filter; (4) OpenAPI `summary=` on all key endpoints; (5) `GET /vehicles` pagination with `limit` (1–100, default 50) and `offset` (≥0, default 0) query params. Write prompt file first, then implement.

### Output summary

**Exception handler** — Created `backend/app/core/exception_handlers.py` with `unhandled_exception_handler(request, exc)`: logs `ERROR` with method, path, and full traceback, returns `JSONResponse(status_code=500, content={"detail": "An unexpected error occurred. Please try again later."})`. Wired into `app` in `main.py` via `app.add_exception_handler(Exception, unhandled_exception_handler)`.

**pyproject.toml entrypoint** — Added `[tool.fastapi]` section with `app = "app.main:app"` so `fastapi dev` resolves the application without explicit path argument.

**vehicle_id validation** — Three-point enforcement:
- `TelemetryEventIn.vehicle_id: Annotated[str, Field(min_length=1, max_length=20)]` in `app/schemas/telemetry.py`
- `vehicle_id: Annotated[str, Path(min_length=1, max_length=20)]` in `PATCH /vehicles/{vehicle_id}/status` route
- `vehicle_id: Annotated[str | None, Query(max_length=20)]` in `GET /anomalies` filter

**OpenAPI summaries** — Added `summary=` to all six endpoints:
- `POST /telemetry` → "Ingest a telemetry event"
- `GET /fleet/state` → "Per-status vehicle counts"
- `GET /zones/counts` → "Entry counts for all 20 zones"
- `GET /vehicles` → "All known vehicles, paginated"
- `PATCH /vehicles/{vehicle_id}/status` → "Update vehicle status; fault cancels active mission"
- `GET /anomalies` → "Query anomaly events with optional filters"

**Pagination on GET /vehicles** — `get_all_vehicle_states` in `vehicle_repository.py` now accepts `limit` and `offset`; service layer threads them through; router exposes them as typed `Query` params. Added `test_vehicles_pagination_limit` integration test.

### Corrections and redirections

- `app.add_exception_handler(Exception, unhandled_exception_handler) # type: ignore[arg-type]` — mypy flagged the inline ignore as unused (`unused-ignore`) after confirming the installed FastAPI version accepts `Exception` without type error. Fix: removed the `# type: ignore` comment.
- Long `@router.get(...)` decorators in `anomaly.py` and `fleet.py` exceeded the 100-char ruff line limit after `summary=` was added. Fix: split each decorator across multiple lines.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `app/core/exception_handlers.py` exists with `unhandled_exception_handler` | ✅ |
| `app.add_exception_handler(Exception, ...)` in `main.py` | ✅ |
| `[tool.fastapi] app = "app.main:app"` in `pyproject.toml` | ✅ |
| `vehicle_id` validated in schema, path, and query filter | ✅ |
| All 6 endpoints have `summary=` | ✅ |
| `GET /vehicles` accepts `limit` and `offset` | ✅ |
| `test_vehicles_pagination_limit` passes | ✅ |
| `pytest -v` | ✅ 24 passed |
| `ruff check .` / `mypy app/` | ✅ All checks passed |

---

## Interaction 15 — Prompt 15: Observability — Structured Logging

### Prompt issued

> Add structured logging throughout the stack: JSON formatter via `python-json-logger` configurable by `LOG_FORMAT` env; `RequestLoggingMiddleware` that propagates/generates `X-Request-Id` and logs method, path, status code, and duration; structured `extra={}` business-event logs in `telemetry` and `vehicle` services; update exception handler to include `request_id`; set `LOG_FORMAT: json` in docker-compose backend env. Prompt file first, then implement.

### Output summary

**`python-json-logger>=3.2`** added to `requirements.txt`.

**`Settings.log_format`** added to `config.py` (default `"json"`; override to `"text"` locally via `.env`).

**`app/core/logging_config.py`** — `setup_logging(level, fmt)` configures root logger:  
- `fmt="json"` → `JsonFormatter` from `pythonjsonlogger.json` (machine-readable output for Docker/prod)  
- `fmt="text"` → standard `Formatter` for human-readable local dev  
Replaces `logging.basicConfig` call in `main.py`.

**`app/middleware/request_logging.py`** — `RequestLoggingMiddleware(BaseHTTPMiddleware)`:  
Reads `X-Request-Id` header or generates `uuid4()`; calls next handler; logs `http_request` event with `request_id`, `method`, `path`, `status_code`, `duration_ms`; echoes `X-Request-Id` on response.  
Added to `app` in `main.py` before `CORSMiddleware`.

**`docker-compose.yml`** — `LOG_FORMAT: json` added to backend env; backend `healthcheck` added (`curl -f http://localhost:8000/health`, 6 retries, 15s start_period); frontend `depends_on` upgraded to `condition: service_healthy` so nginx only starts after uvicorn is ready.

**Business-event logs in services:**
- `telemetry.py` — `logger.info("telemetry_ingested", extra={event_id, vehicle_id, status, battery_pct, zone_entered, anomalies_detected})`
- `vehicle.py` — `logger.info("vehicle_status_updated", extra={vehicle_id, new_status, mission_cancelled})`

**`exception_handlers.py`** — refactored to `logger.error("unhandled_exception", extra={request_id, method, path, error})`.

### Corrections and redirections

- Import `from pythonjsonlogger.jsonlogger import JsonFormatter` triggered `DeprecationWarning` — library moved to `pythonjsonlogger.json` in v3. Fix: updated import to `from pythonjsonlogger.json import JsonFormatter`.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `python-json-logger` in requirements.txt | ✅ |
| `log_format` setting in `config.py` | ✅ |
| `setup_logging()` in `logging_config.py`, called from `main.py` | ✅ |
| `RequestLoggingMiddleware` — `X-Request-Id` on every response | ✅ |
| `telemetry_ingested` log with structured extra fields | ✅ |
| `vehicle_status_updated` log with structured extra fields | ✅ |
| Exception handler uses `request_id` from header | ✅ |
| `LOG_FORMAT: json` in docker-compose backend env | ✅ |
| Backend healthcheck + frontend `service_healthy` condition | ✅ |
| `pytest -v` | ✅ 24 passed |
| `ruff check .` / `mypy app/` | ✅ All checks passed (36 source files) |

---

## Interaction 16 — Prompt 16: Test Completion and Vehicle Detail Endpoint

### Prompt issued

> Close three gaps in one pass: (1) fill the empty `tests/unit/` folder with pure-function unit tests for all 5 anomaly rules; (2) add validation contract tests (422 on invalid vehicle_id lengths, limit=0, limit=101, anomaly filter too long); add offset pagination test; (3) add `GET /vehicles/{vehicle_id}` endpoint returning 200 or 404. Create prompt file first, then implement.

### Output summary

**Unit tests — `tests/unit/test_anomaly_rules.py`** (17 tests):
- Local `make_event(**overrides)` helper builds `TelemetryEventIn` directly (not dict).
- Each of 5 rules tested at boundary values: `check_low_battery` (boundary at 14 vs 15), `check_critical_battery` (4 vs 5), `check_fault_entered` (fault vs idle/moving/charging via `@pytest.mark.parametrize`), `check_speed_anomaly` (0.6+idle vs 0.5+idle vs 1.0+moving), `check_error_codes` (present, empty, multiple).
- Pipeline tests: `ANOMALY_RULES` has exactly 5 entries; multi-anomaly event (battery_pct=4, status=FAULT, error_codes=["E01"]) detects ≥4 types.

**Validation contract tests — `tests/integration/test_validation.py`** (5 tests):
- `POST /telemetry` with `vehicle_id=""` → 422
- `POST /telemetry` with `vehicle_id="x"*21` → 422
- `GET /vehicles?limit=0` → 422
- `GET /vehicles?limit=101` → 422
- `GET /anomalies?vehicle_id=${"x"*21}` → 422

**Offset pagination test** added to `test_fleet_endpoints.py`:
- Finds absolute position of `v-off-a` in sorted list before asserting offset (robust against other test data in shared DB).

**`GET /vehicles/{vehicle_id}` endpoint:**
- `get_vehicle_by_id(vehicle_id, session)` added to `vehicle_repository.py`.
- `get_vehicle(vehicle_id, session)` added to `services/vehicle.py` — raises `VehicleNotFound` if absent.
- `GET /vehicles/{vehicle_id}` route added to `routers/vehicle.py` before `PATCH /{vehicle_id}/status`.
- Two integration tests: found (200 + correct body) and not found (404).

### Corrections and redirections

- `test_vehicles_pagination_offset` initially asserted `v-off-a` is at absolute offset 0, but the shared SQLite DB already contained `v-a01` from a prior test, which sorts before `v-off-a`. Fix: dynamically find the index of `v-off-a` in the full sorted list before asserting.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `tests/unit/test_anomaly_rules.py` — all 5 rules + pipeline | ✅ 17 unit tests |
| `tests/integration/test_validation.py` — 5 contract tests | ✅ |
| `test_vehicles_pagination_offset` — robust offset check | ✅ |
| `GET /vehicles/{vehicle_id}` — 200 or 404 | ✅ |
| Integration tests for new endpoint | ✅ 2 tests |
| `pytest -v` | ✅ 50 passed |
| `ruff check .` / `mypy app/` | ✅ Clean (36 source files) |

---

## Interaction 17 — Prompt 17: Final Polish — Makefile, Prometheus, Health DB Check, .env.example, Observability Tests

### Prompt issued

> Seven gaps in one pass: (1) README API table missing GET /vehicles/{id} and /metrics; (2) .env.example missing LOG_FORMAT; (3) Makefile at repo root with test/lint/up/down/dev targets; (4) GET /health with real SELECT 1 DB check returning 503 on failure; (5) Prometheus metrics via prometheus-fastapi-instrumentator; (6) test for exception handler 500 shape; (7) tests for X-Request-Id propagation. Create prompt file first, then implement.

### Output summary

**`backend/requirements.txt`** — added `prometheus-fastapi-instrumentator>=0.9`.

**`backend/.env.example`** — updated to include `LOG_FORMAT=text` with comment explaining json vs text modes.

**`Makefile` at repo root** — 6 targets with inline `## help` comments:
- `make help` (default) — lists all targets with descriptions
- `make test` — `cd backend && python -m pytest tests/ -v`
- `make lint` — ruff + mypy
- `make up` — `docker compose up --build`
- `make down` — `docker compose down`
- `make dev` — `cd backend && fastapi dev app/main.py`

**`GET /health` with DB readiness** — injects `SessionDep`; executes `SELECT 1`; returns 200 `{"status": "ok"}` on success; logs `WARNING health_check_db_unavailable` and returns 503 `{"status": "unavailable"}` on failure. Makes docker-compose healthcheck semantically meaningful.

**Prometheus metrics** — `Instrumentator().instrument(app).expose(app)` in `main.py` after router registration. Exposes `GET /metrics` with `http_requests_total` and `http_request_duration_seconds` histogram.

**README** — API table updated: added `GET /vehicles/{id}` row, pagination note on `GET /vehicles`, 503 note on `/health`, new `/metrics` row.

**`tests/integration/test_observability.py`** (5 tests):
- `test_unhandled_exception_returns_500_with_safe_body` — patches `app.routers.fleet.get_fleet_state` with `AsyncMock(side_effect=RuntimeError)`; uses inline client with `raise_app_exceptions=False` to receive the 500 response instead of re-raise; asserts status 500, safe body, no stack trace leaked.
- `test_response_always_includes_request_id_header` — any GET /health response must have `x-request-id`.
- `test_provided_request_id_is_echoed_back` — sent `X-Request-Id` must be returned verbatim.
- `test_metrics_endpoint_returns_prometheus_format` — GET /metrics → 200, body contains `http_requests_total`.
- `test_health_returns_ok_when_db_is_up` — GET /health → 200 `{"status": "ok"}`.

### Corrections and redirections

- First patch attempt used `app.services.fleet.get_fleet_state` — mock didn't intercept because the router imported the function at load time. Fix: patched `app.routers.fleet.get_fleet_state` (the binding in the router's namespace).
- `ASGITransport` re-raises server-side exceptions by default in test mode. Fix: created inline client with `raise_app_exceptions=False` for the 500 test, while the fixture client (raise_app_exceptions=True) remains unchanged for all other tests.
- Two ruff E501 violations in `test_anomaly_rules.py` from the previous prompt (parametrize decorator and long assert). Fixed by splitting the decorator args and extracting the assertion to a variable.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| README has `GET /vehicles/{id}`, pagination note, `/metrics` | ✅ |
| `backend/.env.example` has all 4 settings including `LOG_FORMAT` | ✅ |
| `Makefile` at repo root with 6 targets | ✅ |
| `GET /health` executes `SELECT 1`, returns 503 on DB failure | ✅ |
| `GET /metrics` returns 200 with Prometheus text format | ✅ |
| `test_observability.py` — 5 tests (500, request-id x2, metrics, health) | ✅ |
| `pytest -v` | ✅ 55 passed |
| `ruff check .` / `mypy app/` | ✅ Clean (36 source files) |

---

## Interaction 18 — Prompt 18: Prometheus and Grafana in Docker Compose

### Prompt issued

> The backend exposes GET /metrics but no Prometheus server scrapes it. Add prometheus and grafana services to docker-compose.yml so the full observability stack runs with a single `docker compose up --build`. Add prometheus/prometheus.yml scrape config. Update README Quick Start table with all 5 URLs.

### Output summary

**`prometheus/prometheus.yml`** — scrape config with `scrape_interval: 15s`, job `fleet-backend` targeting `backend:8000` at `/metrics`.

**`docker-compose.yml`** — two new services:
- `prometheus` (prom/prometheus:v2.52.0) — mounts `./prometheus/prometheus.yml` read-only, port 9090, `depends_on: backend: condition: service_healthy`.
- `grafana` (grafana/grafana:10.4.3) — port 3000, admin/admin credentials, anonymous viewer enabled (`GF_AUTH_ANONYMOUS_ENABLED=true`, `GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer`), `depends_on: prometheus`.

**README Quick Start table** — expanded from 3 to 5 rows with Notes column; added Grafana datasource setup instruction.

No application code changed — 55 tests still pass.

### Corrections and redirections

None — first attempt clean.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `prometheus/prometheus.yml` with correct scrape target | ✅ |
| `docker-compose.yml` has prometheus + grafana services | ✅ |
| `prometheus` depends on `backend: service_healthy` | ✅ |
| Grafana anonymous viewer access enabled | ✅ |
| README Quick Start shows all 5 URLs with notes | ✅ |
| `pytest -v` | ✅ 55 passed (no app code changed) |

### Post-interaction fix — docker-compose healthcheck

**Bug:** On first `docker compose up --build`, Prometheus and Grafana failed to start with `dependency failed to start: container backend is unhealthy`. Root cause: the healthcheck command `curl -f http://localhost:8000/health` relied on `curl`, which is not installed in `python:3.12-slim`.

**Fix (commit `fix(docker)`):** replaced the `test` with `["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]` — uses Python's stdlib `urllib`, always available in the image. Committed and pushed to `origin/main`.

---

## Interaction 19 — Prompt 19: Grafana Auto-Provisioning

### Prompt issued

> Grafana connects to Prometheus but all dashboards are empty — requires manual datasource setup every time. Add Grafana provisioning files so the datasource and a Fleet dashboard are auto-configured on container start: `grafana/provisioning/datasources/prometheus.yml`, `grafana/provisioning/dashboards/provider.yml`, and `grafana/provisioning/dashboards/fleet.json` with four panels. Mount the provisioning directory in docker-compose.

### Output summary

**`grafana/provisioning/datasources/prometheus.yml`** — provisions Prometheus as the default datasource pointing to `http://prometheus:9090`; `isDefault: true`, `editable: false`.

**`grafana/provisioning/dashboards/provider.yml`** — tells Grafana to load dashboards from `/etc/grafana/provisioning/dashboards` (`disableDeletion: true`, `updateIntervalSeconds: 10`).

**`grafana/provisioning/dashboards/fleet.json`** — Fleet Telemetry dashboard with 4 panels:
- **Request Rate** — `rate(http_requests_total[1m])` Prometheus counter
- **P95 Latency** — `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1m]))`
- **5xx Error Rate** — `rate(http_requests_total{status=~"5.."}[1m])`
- **Requests by Status** — stacked `rate(http_requests_total[1m])` grouped by `status`

Uses `${DS_PROMETHEUS}` template variable with `__inputs` block for proper provisioning-time datasource binding.

**`docker-compose.yml`** — `grafana` service updated to mount `./grafana/provisioning:/etc/grafana/provisioning:ro`.

**README** — removed the "manual datasource setup" instruction; noted that the datasource and dashboard are auto-provisioned.

### Corrections and redirections

- First attempt used `{"type": "prometheus", "uid": "prometheus"}` as a hardcoded datasource reference in `fleet.json`. Grafana provisioning requires the `${DS_PROMETHEUS}` template variable with an `__inputs` block for the datasource to bind correctly at startup. Fix: rewrote the datasource reference using `__inputs` + `${DS_PROMETHEUS}` pattern.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `grafana/provisioning/datasources/prometheus.yml` — Prometheus default datasource | ✅ |
| `grafana/provisioning/dashboards/provider.yml` — dashboard provider config | ✅ |
| `grafana/provisioning/dashboards/fleet.json` — 4 panels, `${DS_PROMETHEUS}` binding | ✅ |
| `docker-compose.yml` mounts provisioning directory | ✅ |
| `docker compose up --build` → Grafana opens with populated dashboard | ✅ |
| `pytest -v` | ✅ 55 passed (no app code changed) |

### Post-interaction fix — Grafana datasource UID mismatch

**Bug:** After running the full stack with `--profile load-test`, all 4 Grafana panels showed "No data" with warning triangles. Prometheus was scraping correctly (`health: up`, last scrape confirmed via API) and metrics existed (`http_requests_total`, `http_request_duration_seconds_bucket`). Root cause: the `${DS_PROMETHEUS}` template variable in `fleet.json` is an **import-time substitution** mechanism (for UI imports) — it is NOT resolved by the Grafana filesystem provisioner. The datasource YAML had no fixed `uid`, so Grafana auto-generated `PBFA97CFB590B2093`; the dashboard panels referenced `${DS_PROMETHEUS}` which remained unresolved, causing all queries to fail silently.

**Fix:** Added `uid: prometheus` to `grafana/provisioning/datasources/prometheus.yml` (makes UID deterministic across container restarts) and replaced all four `"uid": "${DS_PROMETHEUS}"` references in `fleet.json` with `"uid": "prometheus"`. Restarted only the Grafana container (`docker compose restart grafana`) — Locust and the rest of the stack continued running uninterrupted. Dashboard populated immediately after restart.

**Lesson:** For Grafana filesystem provisioning, always use a hardcoded UID in both the datasource YAML and the dashboard JSON. The `${DS_PROMETHEUS}` / `__inputs` pattern is only for dashboards exported from the UI and re-imported manually.

---

## Interaction 20 — Prompt 20: Load Test with Locust

### Prompt issued

> Add Locust as an optional Docker Compose service (profile `load-test`) with a `locustfile.py` that exercises all API endpoints with realistic weights. Serves dual purpose: load test (throughput, latency, error rate) and data population (generates metric traffic so Grafana panels light up within ~30 s). `docker compose --profile load-test up --build` starts the full stack + Locust UI. Create prompt file first, then implement.

### Output summary

**`.claude/prompts/20-load-test-locust.md`** — prompt file created before implementation (per workflow rule).

**`load-test/locustfile.py`** — `FleetApiUser(HttpUser)` with 7 tasks:

| Task | Weight | Endpoint |
|------|--------|----------|
| `post_telemetry` | 10 | `POST /telemetry` |
| `get_fleet_state` | 3 | `GET /fleet/state` |
| `get_vehicles` | 2 | `GET /vehicles` |
| `get_zone_counts` | 2 | `GET /zones/counts` |
| `get_anomalies` | 2 | `GET /anomalies` |
| `get_vehicle_by_id` | 2 | `GET /vehicles/{id}` |
| `get_health` | 1 | `GET /health` |

`wait_time = between(0.05, 0.3)` — aggressive enough to produce visible metrics in Grafana within 30 seconds. Uses all 50 vehicle IDs (`v-01` through `v-50`), 20 real zone names from `app/core/zones.py`, and excludes `fault` from `STATUSES` to avoid mission cancellation side-effects contaminating the dataset.

**`docker-compose.yml`** — `locust` service added with `profiles: ["load-test"]`, image `locustio/locust:2.29.0`, port 8089, depends on `backend: condition: service_healthy`. Not started by the default `docker compose up`.

**`Makefile`** — `load-test` target added: `docker compose --profile load-test up --build`.

**`README.md`** — "Load test + metric population" section added after Quick Start with `docker compose --profile load-test up --build` command, 6-URL table including Locust at http://localhost:8089, and instructions (open Locust → set 20 users + spawn rate 5 → Start swarming → Grafana lights up in ~30 s). Observability section updated: removed stale "natural next additions" bullet for Prometheus (now implemented); updated to accurately describe the current stack.

### Corrections and redirections

None — first attempt clean.

### Acceptance criteria

| Criterion | Result |
|-----------|--------|
| `load-test/locustfile.py` — 7 tasks with correct weights | ✅ |
| Zone names match `app/core/zones.py` (20 zones) | ✅ |
| `fault` excluded from STATUSES | ✅ |
| `locust` service in `docker-compose.yml` behind `load-test` profile | ✅ |
| `make load-test` target in Makefile | ✅ |
| README documents load-test workflow with 6-URL table | ✅ |
| `pytest -v` | ✅ 55 passed (no app code changed) |

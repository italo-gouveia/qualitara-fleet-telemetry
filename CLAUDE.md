# Fleet Telemetry Monitor

Real-time fleet monitoring service for 50 autonomous industrial vehicles.
Take-home challenge — Python FastAPI backend + React/TypeScript frontend.

## Quick Start

```bash
# Backend
cd backend
uv sync                        # or: pip install -r requirements.txt
uvicorn app.main:app --reload  # http://localhost:8000

# Run tests
pytest

# Lint + type-check
ruff check . && mypy .

# Frontend
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| **Language** | Python 3.12 | Challenge requirement, async-native with FastAPI |
| **Web framework** | FastAPI + Uvicorn | Async-first, automatic OpenAPI, Pydantic v2 validation |
| **Database** | PostgreSQL (default) / SQLite (dev) | See [ADR](docs/ADR.md) — Postgres for correct concurrent writes, SQLite for zero-setup local dev |
| **ORM** | SQLAlchemy 2.x async | Async sessions, explicit transaction control |
| **Migrations** | Alembic | Pairs with SQLAlchemy, version-controlled schema |
| **Frontend** | React 18 + TypeScript + Vite | Challenge requirement |
| **State / fetching** | TanStack Query (React Query) | Server-state, polling, cache invalidation |
| **Testing** | pytest + pytest-asyncio + httpx | Async-safe, fast, HTTPX for ASGI transport |
| **Lint** | Ruff + Mypy | Single fast tool covers import sort, style, types |

## Architecture

### Directory Structure

```
qualitara-fleet-telemetry/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, lifespan, CORS
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # Engine, session factory, Base
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # One file per resource group
│   │   ├── services/            # Business logic (pure, no HTTP)
│   │   ├── repositories/        # DB queries (repository pattern)
│   │   └── core/
│   │       ├── anomaly.py       # Anomaly detection rules
│   │       └── zones.py         # ZONES constant + zone logic
│   └── tests/
│       ├── unit/
│       └── integration/
├── frontend/
│   └── src/
│       ├── components/
│       ├── hooks/               # Custom hooks (useFleet, useAnomalies, useZones)
│       ├── api/                 # Typed API client
│       └── types/               # Shared TS types
├── docs/
│   ├── ADR.md                   # Architecture Decision Record
│   └── AI_INTERACTION_LOG.md    # AI usage log (required deliverable)
├── .claude/
│   ├── agents/                  # Specialist agent charters
│   ├── rules/                   # Enforceable coding rules
│   ├── skills/                  # Reusable skill prompts
│   ├── prompts/                 # Ordered implementation prompts
│   └── context/                 # Challenge spec + domain notes
├── .global-context/             # Cross-project context (committed)
└── .local-context/              # Personal spikes + notes (gitignored)
```

### Key Domain Concepts

- **Vehicle**: one of 50 autonomous vehicles; emits telemetry at 1 Hz
- **Telemetry event**: `vehicle_id`, `timestamp`, `lat/lon`, `battery_pct`, `speed_mps`, `status`, `error_codes`, `zone_entered`
- **Status**: `idle | moving | charging | fault`
- **Zone**: one of 20 named areas (hardcoded `ZONES` constant); `zone_entered` is non-null only on the event where the vehicle first crosses into it
- **Anomaly**: detected in real-time on ingest; definition documented in ADR
- **Mission**: cancelled atomically when vehicle transitions to `fault`

### Concurrency-Critical Paths

| Operation | Strategy |
|-----------|----------|
| Zone entry count increment | `SELECT ... FOR UPDATE` or DB-level atomic increment |
| Fleet aggregate state | Read from a materialized view or single `SELECT ... GROUP BY` (never in-process counters) |
| Fault → mission cancellation | Single serializable transaction; `SELECT FOR UPDATE` on vehicle row |

## Development Guidelines

### Code Quality

- **Simplicity first**: no premature abstractions — see `.claude/rules/simplicity-first.md`
- **Repository pattern**: all DB access goes through `repositories/`; services never import `Session` directly
- **No business logic in routers**: routers validate input and delegate; services own rules
- **Pydantic v2**: use model validators, not `__init__` overrides; `model_config` not nested `class Config`

### Testing Strategy

- **Unit tests** (`tests/unit/`): pure logic — anomaly rules, schema validation, mapping functions; no DB, no HTTP
- **Integration tests** (`tests/integration/`): full ASGI stack via `httpx.AsyncClient(app=app, base_url="http://test")` with a real (SQLite in-memory or Postgres test DB) — see `.claude/rules/integration-testing-guide.md`
- **Naming**: `test_<what>_<condition>_<expected_result>` — e.g. `test_ingest_fault_status_cancels_active_mission`
- **No mocks for DB** unless testing external integrations; prefer real transactions that roll back

### Git Workflow

- **Branches**: `feat/<slug>`, `fix/<slug>`, `chore/<slug>`
- **Commits**: Conventional Commits — `feat(telemetry): add zone entry counter`, `fix(api): handle concurrent fault transition`
- **PR title**: mirrors squash commit message

## Configuration

### Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/fleet   # Postgres
# DATABASE_URL=sqlite+aiosqlite:///./fleet.db                       # SQLite dev

SECRET_KEY=changeme          # used for any future auth
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173
```

Copy `.env.example` to `.env` (gitignored). Never commit real credentials.

## Common Tasks

```bash
# Create a new Alembic migration after model change
alembic revision --autogenerate -m "add maintenance_records table"
alembic upgrade head

# Run only integration tests
pytest tests/integration/ -v

# Check types
mypy backend/app --strict

# Format + lint in one pass
ruff format . && ruff check --fix .
```

## Where Things Live (`.claude/`)

| Path | Purpose |
|------|---------|
| `.claude/context/challenge-spec.md` | Full challenge spec verbatim |
| `.claude/context/domain-model.md` | Entity relationships, field types, concurrency notes |
| `.claude/context/tech-decisions.md` | Framework/DB choice rationale (feeds ADR) |
| `.claude/rules/code-quality.md` | Cyclomatic + cognitive complexity limits, SonarQube-style issues, naming |
| `.claude/rules/database.md` | SQLAlchemy async patterns, transaction discipline |
| `.claude/rules/git.md` | Branch, commit, PR conventions |
| `.claude/rules/integration-testing-guide.md` | ASGI test setup, fixtures, patterns |
| `.claude/rules/local-context.md` | What lives in `.local-context/` |
| `.claude/rules/logging.md` | Structured logging, PII, levels |
| `.claude/rules/performance.md` | Big O analysis, N+1 detection, query optimisation, async hygiene |
| `.claude/rules/security.md` | Input validation, secrets, injection |
| `.claude/rules/simplicity-first.md` | KISS/YAGNI discipline |
| `.claude/rules/testing.md` | Test conventions, naming, coverage |
| `.claude/agents/` | Specialist agent charters |
| `.claude/skills/` | Reusable skill prompts |
| `.claude/prompts/` | Ordered implementation prompts (01–10) |

## Deliverables Checklist

- [ ] `POST /telemetry` — ingest endpoint, handles concurrent bursts
- [ ] `GET /vehicles` — current status + battery for all 50 vehicles
- [ ] `GET /vehicles/{id}/anomalies` — anomalies filtered by vehicle + time range
- [ ] `GET /fleet/state` — aggregate per-status counts, concurrency-safe
- [ ] `GET /zones/counts` — per-zone entry counts
- [ ] `PATCH /vehicles/{id}/status` — fault transition → atomic mission cancel + maintenance record
- [ ] React dashboard: live vehicle list, anomalies, zone counts
- [ ] `docs/ADR.md` — 1-page architecture decision record
- [ ] `docs/AI_INTERACTION_LOG.md` — AI usage log
- [ ] `README.md` — how to run locally

## API Documentation

FastAPI auto-generates OpenAPI at `/docs` (Swagger UI) and `/redoc`.
Run the backend and open `http://localhost:8000/docs`.

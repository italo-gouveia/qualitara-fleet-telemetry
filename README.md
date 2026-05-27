# Fleet Telemetry Monitor

Real-time monitoring service for 50 autonomous industrial vehicles emitting telemetry at 1 Hz.

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.x async, Alembic |
| Database | PostgreSQL (production) / SQLite + aiosqlite (dev/tests) |
| Frontend | React 18, TypeScript, Vite, TanStack Query v5 |
| Tests | pytest-asyncio, httpx ASGITransport |

## How to Run

### Quick Start with Docker Compose (recommended)

Requires Docker Desktop (or Docker Engine + Compose v2).

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:5173 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 (user/pass/db: `fleet`) |

The backend waits for PostgreSQL to pass its healthcheck, runs `alembic upgrade head` automatically, then starts Uvicorn. Zones are seeded on first startup.

To populate the dashboard with live data, run the simulator in a separate terminal while the stack is up:

```bash
python backend/scripts/simulate_fleet.py
```

To stop and remove containers (data volume is preserved):

```bash
docker compose down
```

To also wipe the database volume:

```bash
docker compose down -v
```

---

### Manual Setup (local development, SQLite)

### Backend

```bash
cd backend

# Install dependencies
pip install -e ".[dev]"

# Apply migrations (creates fleet.db with SQLite by default)
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload
```

API available at **http://localhost:8000**  
Swagger UI at **http://localhost:8000/docs**

To use PostgreSQL instead of SQLite, set the environment variable:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/fleet uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard available at **http://localhost:5173**

> The frontend polls the backend every 2 seconds. Start the backend first.

### Simulate Fleet (optional)

With the backend running, start the simulator to populate the dashboard with live data:

```bash
python backend/scripts/simulate_fleet.py
# or point at a different host:
python backend/scripts/simulate_fleet.py --url http://localhost:8000
```

50 virtual vehicles will begin sending telemetry at 1 Hz. Zone counts increase, anomalies appear (low battery, fault transitions), and the dashboard updates in real time.

### Run Tests

```bash
cd backend
pytest -v          # 23 integration tests
ruff check .       # linting
mypy app/          # type checking
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./fleet.db` | DB connection string |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed frontend origins (JSON list) |

Set via a `.env` file in `backend/` (gitignored) or as shell environment variables.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/telemetry` | Ingest a telemetry event (201) |
| `GET` | `/fleet/state` | Per-status vehicle counts |
| `GET` | `/vehicles` | All known vehicles, ordered by ID |
| `GET` | `/zones/counts` | Entry counts for all 20 zones |
| `GET` | `/anomalies` | Anomalies with optional filters: `vehicle_id`, `start`, `end`, `limit` |
| `PATCH` | `/vehicles/{id}/status` | Update vehicle status; cancels active mission on fault |
| `GET` | `/health` | Liveness check |
| `GET` | `/docs` | Swagger UI |

## Architecture

See [docs/ADR.md](docs/ADR.md) for the three key design decisions:
1. PostgreSQL vs SQLite — atomicity requirements
2. Polling vs WebSocket — scope and latency trade-off
3. Synchronous anomaly detection — simplicity vs. decoupled queue

## Concurrency-Critical Paths

| Path | Mechanism |
|------|-----------|
| Zone counter increment | `UPDATE … SET entry_count = entry_count + 1` — single atomic SQL, no ORM read-modify-write |
| Fault → mission cancel | `SELECT FOR UPDATE` on VehicleState + Mission in one transaction |
| VehicleState upsert | `INSERT … ON CONFLICT DO UPDATE` — no separate SELECT |
| Fleet aggregate | `SELECT status, COUNT(*) GROUP BY status` — DB-side, safe under concurrent updates |

## AI Usage

This project was built with **Claude Code** (Anthropic, `claude-sonnet-4-6`) via the CLI. See [docs/AI_INTERACTION_LOG.md](docs/AI_INTERACTION_LOG.md) for a full log of every interaction, corrections made, and a reflection on what AI was and wasn't good at.

# Tech Decisions — Context for ADR

Pre-decided choices and their rationale. These should be reflected in `docs/ADR.md`.

---

## 1. Database: PostgreSQL (default) / SQLite (dev-only)

**Decision**: PostgreSQL for correctness under concurrency; SQLite acceptable for zero-setup local development only.

**Why Postgres wins**:
- Atomic `UPDATE … SET count = count + 1` for zone counters — no race condition
- `SELECT … FOR UPDATE` with `REPEATABLE READ` or `SERIALIZABLE` for the fault→mission transition
- Row-level locking is production-safe at scale
- `JSONB` for `error_codes` with indexing if needed

**Why SQLite is kept for dev**:
- Zero-setup, in-memory option for CI/unit tests
- Same SQLAlchemy async API (`aiosqlite` driver)
- SQLite WAL mode handles limited concurrency; sufficient for local testing
- Clearly documented as dev-only

**Consequence**: `DATABASE_URL` env var selects driver; schema must be DB-agnostic (avoid Postgres-only JSONB ops in queries unless guarded).

---

## 2. Polling vs WebSocket for Dashboard

**Decision**: Polling (short interval, ~2s) for the initial implementation.

**Why**:
- Simpler to implement correctly within the 5–6h budget
- TanStack Query handles stale-while-revalidate automatically
- WebSocket adds connection lifecycle, reconnection, and backpressure complexity
- 50 vehicles × 1 Hz = 50 events/s; a 2s poll returns a ~100-event batch — acceptable latency for a dashboard
- WebSocket is a documented follow-up (mentioned in ADR)

**Tradeoff**: 2s polling latency vs true push. Acceptable for a monitoring dashboard; not for safety-critical control.

---

## 3. Anomaly Detection: In-Process, Rule-Based

**Decision**: synchronous rule evaluation inside the ingest request handler, before responding.

**Why**:
- No message queue needed in a 5–6h challenge
- Rules are pure functions: easy to test, extend, and reason about
- Latency is negligible (microseconds per event)
- Result stored immediately in `anomalies` table

**Tradeoff at scale**: at 1000s of vehicles, a queue (e.g. Kafka) would decouple ingest from detection. Documented in ADR.

---

## 4. ORM: SQLAlchemy 2.x Async

**Decision**: SQLAlchemy async core + ORM with explicit sessions.

**Why**:
- Alembic migrations pair naturally
- Async sessions work with both asyncpg (Postgres) and aiosqlite (SQLite)
- Explicit `async with session.begin()` makes transaction boundaries visible
- Avoids hidden N+1 with lazy loading disabled by default in async mode

**Key rule**: Never use `session.execute(text(...))` for business logic — always ORM or `select()` expressions.

---

## 5. FastAPI over Django REST

**Decision**: FastAPI.

**Why**:
- Async-native (ASGI); no `sync_to_async` wrappers needed
- Pydantic v2 validation built-in; automatic OpenAPI
- Lifespan events for DB engine setup/teardown
- Lighter than Django for an API-only service with no admin panel
- `httpx.AsyncClient(app=app)` for zero-infrastructure integration tests

---

## 6. Scale Threshold Defined as "10× current" (500 vehicles, 500 events/s)

**What would change**:
- Zone counts: still fine with Postgres row-lock, but a Redis INCR may be faster under extreme contention
- Telemetry ingest: consider a write-ahead queue (Kafka/Redis Streams) to buffer bursts; decouple ingest from anomaly detection
- Fleet state: a materialized view refreshed every N seconds rather than live GROUP BY
- Deployment: multiple Uvicorn workers behind a load balancer; async DB connection pool tuning
- Frontend: switch polling → WebSocket or SSE for true push

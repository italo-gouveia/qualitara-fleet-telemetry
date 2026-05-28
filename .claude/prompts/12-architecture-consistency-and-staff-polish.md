# Prompt 12 — Architecture Consistency & Staff-Level Polish

## Motivation (self-review)

A self-review pass against the delivered codebase surfaced two code issues and one documentation gap that should be resolved before submission.

---

## Issue 1 — Inconsistent layering: routers calling repositories directly

### Problem

`vehicle.py` router correctly uses `routes → service → repository`. The other three routers break this pattern:

| Router | Current | Expected |
|--------|---------|----------|
| `routers/telemetry.py` | router → service ✅ | |
| `routers/vehicle.py` | router → service → repo ✅ | |
| `routers/fleet.py` | router → **repo directly** ❌ | router → service → repo |
| `routers/anomaly.py` | router → **repo directly** ❌ | router → service → repo |

### Fix

Create `app/services/fleet.py` and `app/services/anomaly.py`. Move all repository calls and mapping logic into those services. Routers become thin: inject session, call service, return result.

**`app/services/fleet.py`**:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.vehicle_repository import get_all_vehicle_states, get_fleet_aggregate
from app.repositories.zone_repository import get_all_zone_counts
from app.schemas.fleet import FleetStateResponse, VehicleStateResponse


async def get_fleet_state(session: AsyncSession) -> FleetStateResponse:
    return await get_fleet_aggregate(session)


async def get_vehicles(session: AsyncSession) -> list[VehicleStateResponse]:
    return await get_all_vehicle_states(session)


async def get_zone_counts(session: AsyncSession) -> dict[str, int]:
    return await get_all_zone_counts(session)
```

**`app/services/anomaly.py`**:
```python
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.anomaly_repository import get_anomalies
from app.schemas.anomaly import AnomalyResponse


async def query_anomalies(
    session: AsyncSession,
    vehicle_id: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
) -> list[AnomalyResponse]:
    rows = await get_anomalies(session, vehicle_id=vehicle_id, start=start, end=end, limit=limit)
    return [
        AnomalyResponse(
            id=row.id,
            vehicle_id=row.vehicle_id,
            detected_at=row.detected_at,
            type=row.type,
            detail=row.detail,
        )
        for row in rows
    ]
```

Update `routers/fleet.py` and `routers/anomaly.py` to import from services only.

---

## Issue 2 — `Base.metadata.create_all` in lifespan duplicates Alembic's role

### Problem

`main.py` lifespan runs `Base.metadata.create_all` at startup. This works but puts schema management in two places (Alembic migrations + ORM reflection), creating a potential drift surface.

### Fix

Remove `create_all` from lifespan. Alembic is already the sole schema owner (`entrypoint.sh` runs `alembic upgrade head`; `conftest.py` runs `create_all` independently for in-memory SQLite tests). Keep `_seed_zone_counts()` and `engine.dispose()`.

Remove imports that were only needed for `create_all`: `Base`, `engine` (keep engine for dispose), and the model `noqa: F401` block (models are imported by their repos at runtime; Alembic has its own model import in `env.py`).

---

## Issue 3 — README does not yet sell a staff/principal solution

### Fix: rewrite README with the following sections

1. **Header + one-liner problem statement**
2. **Architecture overview** — ASCII diagram showing data flow end-to-end
3. **Stack table** (keep, add Alembic and asyncpg)
4. **Quick Start (Docker)** — keep current
5. **Manual Setup** — keep current
6. **API Endpoints** — keep current
7. **Concurrency-Critical Paths** — keep current
8. **Scalability Roadmap** — brief, concrete: what changes at 10×/500 vehicles
9. **Observability** — what's in (health, structured logs) and what's next (Prometheus, OTEL)
10. **Non-Goals** — shows design maturity; list 5–6 items explicitly out of scope
11. **Architecture Decisions** — one-line summary + link to ADR.md
12. **AI Usage** — reframe: AI as coding accelerator; architecture, trade-offs and engineering decisions made by the developer

### Architecture diagram (ASCII, to embed in README)

```
 Telemetry Sources (50 vehicles × 1 Hz)
          │
          │  POST /telemetry
          ▼
 ┌─────────────────────────────────────────┐
 │         FastAPI (Python 3.12)           │
 │  router → service → repository         │
 │                                         │
 │  • Atomic zone counter (UPDATE +1)      │
 │  • Vehicle upsert (ON CONFLICT UPDATE)  │
 │  • Fault → mission cancel (FOR UPDATE)  │
 │  • Anomaly detection (sync, in-txn)     │
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

### Scalability Roadmap section

```markdown
## Scalability Roadmap

Current design handles 50 vehicles at 1 Hz comfortably on a single Postgres instance.
At 10× (500 vehicles, ~500 events/s) the following changes apply:

| Bottleneck | Current | At Scale |
|-----------|---------|----------|
| Ingest throughput | Synchronous DB write per request | Write-ahead queue (Kafka / Redis Streams); async consumer group |
| Zone counters | PostgreSQL row lock | Redis `INCR` (lock-free, sub-ms); periodic DB sync |
| Fleet aggregate | Live `GROUP BY` on every poll | Materialized view refreshed every N seconds |
| Dashboard delivery | HTTP polling every 2s | Server-Sent Events or WebSocket + Redis Pub/Sub |
| Anomaly detection | Synchronous in-request | Consumer group with dedicated detection workers |
| Database | Single Postgres instance | Read replicas for query endpoints; pgBouncer connection pool |
```

### Non-Goals section

```markdown
## Non-Goals

These are explicitly out of scope for this implementation, not forgotten:

| Feature | Rationale |
|---------|-----------|
| Authentication / API keys | Not required by spec; would add ~1 h scope |
| Rate limiting on ingest | Useful in production; not required by spec |
| WebSocket real-time push | Polling is sufficient; WebSocket adds reconnection complexity |
| Zone geometry / collision detection | Spec delegates this to the edge client |
| Historical time-series analytics | DB schema supports it; not required |
| Multi-tenant / per-fleet isolation | Single fleet per deployment; spec is explicit |
```

---

## Deferred (out of scope for this prompt)

| Suggestion | Status |
|-----------|--------|
| TestContainers in CI | Valuable but requires Docker-in-Docker in CI and doubles test time; documented as next step in ADR |
| Repository-as-class with constructor injection | Cleaner DI; deferred to avoid a full-repo refactor within the challenge window |

---

## Acceptance Criteria

- [ ] `app/services/fleet.py` and `app/services/anomaly.py` exist
- [ ] All four routers follow `router → service → repository`
- [ ] `Base.metadata.create_all` removed from `main.py` lifespan
- [ ] `pytest -v` still passes — 23 tests
- [ ] `ruff check .` and `mypy app/` clean
- [ ] README has: architecture diagram, scalability roadmap, observability, non-goals, reframed AI usage
- [ ] Add Interaction 12 to `docs/AI_INTERACTION_LOG.md`

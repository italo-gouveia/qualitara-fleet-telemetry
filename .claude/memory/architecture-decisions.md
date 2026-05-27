---
name: architecture-decisions
description: "Settled architectural decisions — DB, polling, anomaly detection, ORM — do not re-open without a reason"
type: project
---

# Architecture Decisions (Settled)

## Database: PostgreSQL + SQLite dev

PostgreSQL required for correct `SELECT FOR UPDATE` and atomic `UPDATE ... SET count = count + 1`.
SQLite acceptable for zero-setup local development only (aiosqlite driver).

**Why**: Row-level locking and atomic UPDATE are non-negotiable for the zone counter and fault transition.

**How to apply**: Never implement the zone counter as a Python read-modify-write. Never use in-process counters for fleet aggregate.

## Polling: 2s interval, not WebSocket

TanStack Query `refetchInterval: 2000` on all live queries.

**Why**: 50 vehicles × 1 Hz = trivially small data rate; 2s latency acceptable for monitoring dashboard. WebSocket adds reconnection complexity not justified in 5–6h scope.

**How to apply**: Do not switch to WebSocket unless explicitly requested.

## Anomaly Detection: In-process, rule list

`ANOMALY_RULES: list[Callable[[TelemetryEventIn], AnomalyType | None]]` evaluated synchronously in ingest handler.

**Why**: Pure functions, microsecond evaluation, direct DB insert in same transaction. No queue needed at 50 vehicles.

**How to apply**: Add new rules by appending to `ANOMALY_RULES` list. Never add a message queue for this scale.

## ORM: SQLAlchemy 2.x async

`mapped_column()` + `Mapped[T]` annotations, `async with session.begin()` for explicit transactions, `expire_on_commit=False` in session factory.

**How to apply**: All DB access through repository classes. Services never hold `AsyncSession` directly.

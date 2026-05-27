# Prompt 08 — ADR and AI Interaction Log

## Goal

Write the two required non-code deliverables: `docs/ADR.md` and `docs/AI_INTERACTION_LOG.md`.

## Context to Read

- `.claude/context/tech-decisions.md` — pre-decided choices with rationale
- `.claude/context/challenge-spec.md` — what the ADR must answer

---

## `docs/ADR.md` — Template

```markdown
# Architecture Decision Record
## Fleet Telemetry Monitoring Service

---

### Decision 1: PostgreSQL with SQLite fallback for local development

**Context**: 50 vehicles at 1 Hz generating concurrent writes; zone counters and fault transitions require atomicity.

**Decision**: PostgreSQL as the primary database. SQLite with aiosqlite for zero-setup local development only.

**Why**: PostgreSQL's row-level locking (`SELECT FOR UPDATE`) and atomic UPDATE expressions (`SET count = count + 1`) are essential for the zone counter and fault transition requirements. SQLite's WAL mode handles limited concurrency but lacks `SKIP LOCKED` and has weaker isolation guarantees.

**Tradeoff**: Requires a running Postgres for production-correct concurrency tests. Mitigated by clear documentation and Docker Compose.

---

### Decision 2: Short-interval polling (2s) over WebSocket

**Context**: Dashboard must show live vehicle status + zone counts.

**Decision**: TanStack Query polling at 2-second intervals.

**Why**: 50 vehicles at 1 Hz produces 50 events/second — a 2s poll returns a small batch with acceptable latency for a monitoring display. WebSocket adds reconnection logic, backpressure handling, and state synchronization complexity that isn't justified in a 5–6 hour scope.

**What would change at scale**: with 500+ vehicles or sub-second display requirements, replace with Server-Sent Events or WebSocket + a publish/subscribe layer (e.g. Redis Pub/Sub).

---

### Decision 3: In-process synchronous anomaly detection

**Context**: Anomaly detection must happen in real-time on ingest.

**Decision**: Run rules synchronously inside the ingest request handler, before responding.

**Why**: Rule evaluation is O(1) pure functions taking microseconds. No queue needed at this scale. Direct insert to `anomalies` table in the same transaction guarantees consistency.

**Tradeoff**: At 500+ vehicles with complex ML rules, a queue (Kafka, Redis Streams) would decouple detection latency from ingest throughput. Documented as a known future step.

---

### Unclear Constraints and Assumptions

| Assumption | Reasoning |
|------------|-----------|
| One active mission per vehicle at most | Spec says "active mission" (singular) |
| zone_entered from vehicle edge, not validated server-side | Spec says "assume edge client populates correctly" |
| No authentication required | Not mentioned in spec |
| 50 vehicles is a fixed fleet (not growing) | Spec says "50 autonomous industrial vehicles" |
| Anomaly definition is implementation choice | Spec says "your definition — justify it" |

---

### What Would Change at 10× Scale (500 vehicles, 500 events/s)

1. **Ingest**: introduce a write-ahead queue (Kafka/Redis Streams) to buffer bursts; decouple anomaly detection to a consumer
2. **Zone counters**: Redis INCR (lock-free) instead of Postgres row-lock under high contention
3. **Fleet aggregate**: materialized view refreshed every N seconds rather than live GROUP BY
4. **Frontend**: replace polling with SSE or WebSocket for push-based updates
5. **Database**: read replicas for query endpoints; connection pool tuning

---

### Deliberately Left Out

| Feature | Why |
|---------|-----|
| Authentication / API keys | Not in spec; would add ~1h of scope |
| Rate limiting on ingest | Would add middleware complexity; noted for production |
| WebSocket dashboard | Polling sufficient; WebSocket adds reconnection complexity |
| Zone geometry / collision detection | Spec explicitly says edge client handles this |
| Historical telemetry analytics | Not required; the DB schema supports it as a future add |
```

---

## `docs/AI_INTERACTION_LOG.md` — Template

```markdown
# AI Interaction Log

## Tool Used
Claude Code (claude-sonnet-4-6) via CLI

---

## Interaction 1 — Project Bootstrap

**Prompt**: [paste the prompt from .claude/prompts/01-project-bootstrap.md]

**Output**: [summary of what was generated]

**Corrections**: [any redirections you made]

---

## Interaction 2 — Database Models

...

---

## Reflection (3–5 bullets)

- **What AI was good at**: boilerplate generation (Pydantic schemas, FastAPI routers), following explicit patterns from rule files, writing test fixtures
- **Where it failed**: initially wrote the zone counter as a read-modify-write (race condition) — caught and corrected by providing the explicit atomic UPDATE pattern from the database rules
- **What required manual verification**: all concurrency-critical code paths (SELECT FOR UPDATE, atomic increments, transaction boundaries)
- **Prompt engineering insight**: structured rule files and explicit code examples in context dramatically reduced correction cycles
- **Overall**: AI generated ~70% of the implementation; critical safety and concurrency paths required human review and correction
```

## Acceptance Criteria

- ADR answers all 4 required questions from the spec
- AI log has at least 5 meaningful interactions documented
- Reflection has 3–5 bullets
- Both files committed to `docs/`

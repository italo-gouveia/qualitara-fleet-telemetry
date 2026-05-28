# Architecture Decision Record
## Fleet Telemetry Monitoring Service

---

### Decision 1 — PostgreSQL as primary database, SQLite for local development

**Context**

50 autonomous vehicles emit telemetry at 1 Hz (50 events/second sustained). Two operations require strict atomicity under concurrent writes:

1. **Zone counter increment** — multiple vehicles can enter the same zone simultaneously.
2. **Fault → mission cancellation** — updating vehicle status, cancelling the active mission, and creating a maintenance record must happen atomically or not at all.

**Decision**

PostgreSQL is the production database. SQLite with `aiosqlite` is allowed for zero-setup local development and automated tests only.

**Why**

PostgreSQL provides:
- `UPDATE zone_counts SET entry_count = entry_count + 1 WHERE zone_id = :z` — a single atomic SQL statement; no application-level read-modify-write.
- `SELECT … FOR UPDATE` on `VehicleState` to serialize concurrent fault transitions at the DB level, preventing double-cancellation.
- Row-level locking that degrades gracefully at scale (vs. table-level locking in SQLite).
- `JSONB` for `error_codes` and `detail` fields when indexing is eventually required.

SQLite is retained for development ergonomics: same SQLAlchemy async API (`aiosqlite` driver), in-memory mode for fast CI tests, and zero external dependencies in development.

**Trade-off**

Production-correct concurrency tests require a running PostgreSQL instance. SQLite lacks `SKIP LOCKED` and has weaker isolation than `READ COMMITTED`. This is mitigated by clear documentation: SQLite is for development only; CI should target PostgreSQL.

---

### Decision 2 — Short-interval polling (2 s) over WebSocket

**Context**

The dashboard must display live vehicle status, battery levels, zone counts, and anomalies without perceptible lag for a human operator.

**Decision**

TanStack Query polling at a 2-second `refetchInterval` on all read queries.

**Why**

- 50 vehicles × 1 Hz = 50 events/second ingest. A 2 s poll window returns a small result set; latency is acceptable for a monitoring display (not a safety-critical control panel).
- TanStack Query handles stale-while-revalidate, error retries, and deduplication out of the box, with zero additional infrastructure.
- WebSocket requires connection lifecycle management, reconnection logic, backpressure handling, and a server-side broadcast layer — none of which is justified within a 5–6 hour delivery budget.
- Per-vehicle anomaly hooks poll at 5 s since anomaly state changes less frequently than vehicle status.

**What would change at scale**

With 500+ vehicles or sub-second display requirements: replace polling with Server-Sent Events (simpler than WebSocket, no full-duplex needed for dashboard reads) or WebSocket + Redis Pub/Sub for broadcast.

---

### Decision 3 — Synchronous in-process anomaly detection

**Context**

Anomalies must be detected in real-time as telemetry arrives, not in a batch job.

**Decision**

Run anomaly rules synchronously inside the `POST /telemetry` request handler, before responding. Detected anomalies are inserted into the `anomalies` table in the same DB session as the telemetry event.

**Why**

- Each rule is a pure function `(TelemetryEventIn) -> AnomalyType | None` — evaluation takes microseconds and does not block I/O.
- Same-transaction insert guarantees that an anomaly is never detached from the event that triggered it.
- No message queue, worker process, or distributed state needed — dramatically reduces operational complexity within the challenge scope.
- The rule list (`ANOMALY_RULES`) is open for extension without modifying the ingest service (open/closed principle).

**Trade-off at scale**

At 500+ vehicles with computationally heavy rules (ML inference, external lookups), a queue (Kafka, Redis Streams) would decouple ingest throughput from detection latency. The current architecture documents this as the primary future evolution path.

**Anomaly rules implemented**

| Rule | Trigger | Type |
|------|---------|------|
| Low battery | `battery_pct < 15` | `low_battery` |
| Critical battery | `battery_pct < 5` | `critical_battery` |
| Fault status | `status == "fault"` | `fault_entered` |
| Speed while idle | `speed_mps > 0.5 AND status == "idle"` | `speed_anomaly` |
| Error codes present | `len(error_codes) > 0` | `error_code_reported` |

---

### Decision 4 — Frontend testing strategy: unit → integration (MSW) → E2E (Playwright)

**Context**

The React dashboard has no existing tests at the start of development. Testing strategy must be efficient (no real backend needed in CI), realistic (hooks and HTTP layer exercised, not just render), and maintainable.

**Decision**

Three-layer pyramid:
1. **Unit** (Vitest + Testing Library) — hooks mocked at module level (`vi.mock`); tests component rendering in complete isolation.
2. **Integration** (Vitest + MSW + real QueryClient) — MSW intercepts `fetch` at the Node network layer; TanStack Query, hooks, and components all run for real; no mock at the hook level.
3. **E2E** (Playwright / Chromium) — full browser rendering with `page.route()` mocking all API calls; exercises routing, CSS classes, DOM structure, and cross-component interaction.

**Why**

- MSW is the standard React Testing Library recommendation for integration tests — it tests the real HTTP stack without a live server.
- `page.route()` in Playwright means E2E tests never require the FastAPI backend; they run entirely offline and in CI with a Vite dev server.
- Separating the test tsconfig scope (`tsconfig.app.json` excludes `src/test`) keeps `tsc -b` fast and focused on production code; Vitest handles test-file type transforms independently.
- `vitest/config` (instead of `vite`) is used in `vite.config.ts` so the `test:` block is correctly typed without polluting the app tsconfig.

**Trade-off**

No TestContainers — the backend integration tests use in-memory SQLite, not real PostgreSQL. SQLite covers most cases but has weaker isolation guarantees (see Decision 1). This is a known and documented limitation, acceptable within the challenge scope.

---

### Unclear Constraints and Assumptions

| Assumption | Reasoning |
|------------|-----------|
| One active mission per vehicle at most | Spec says "cancel active mission" (singular) |
| `zone_entered` is populated by the edge client, not validated server-side | Spec states edge client detects zone transitions |
| No authentication or API keys required | Not mentioned in the spec |
| Fleet size is fixed at 50 vehicles | Spec says "50 autonomous industrial vehicles" |
| Anomaly definition is the implementer's choice | Spec says "your definition — justify it in the ADR" |
| `zone_entered` is non-null only on the first tick of a zone crossing | Spec: "non-null only on the first event where the vehicle crosses into a new zone" |

---

### What Would Change at 10× Scale (500 vehicles, ~500 events/s)

1. **Ingest throughput**: introduce a write-ahead queue (Kafka or Redis Streams) in front of the DB write; decouple anomaly detection to a consumer group so a slow rule does not block the HTTP response.
2. **Zone counters**: Redis `INCR` (lock-free, sub-millisecond) instead of PostgreSQL row-lock under high contention; sync to DB periodically or on flush.
3. **Fleet aggregate**: materialized view refreshed every N seconds instead of live `GROUP BY` on every dashboard poll.
4. **Frontend**: replace polling with Server-Sent Events or WebSocket; the server pushes diffs rather than the client re-fetching the full vehicle list.
5. **Database**: read replicas for query endpoints (`/fleet/state`, `/zones/counts`, `/vehicles`, `/anomalies`); connection pool tuning (pgBouncer); partitioned `telemetry_events` by time range.
6. **Deployment**: multiple Uvicorn workers behind a load balancer (gunicorn + uvicorn workers); async connection pool configured for worker count.

---

### Deliberately Left Out

| Feature | Why |
|---------|-----|
| Authentication / API keys | Not mentioned in spec; would add ~1 hour of scope |
| Rate limiting on ingest | Useful in production; not required by spec; noted for future |
| WebSocket dashboard | Polling is sufficient; WebSocket adds reconnection complexity out of scope |
| Zone geometry / collision detection | Spec explicitly delegates this to the edge client |
| Historical telemetry analytics / time-series | DB schema supports it as a future add; not required |
| `PATCH /vehicles/{id}/mission` — manual mission control | Not required; inferred from spec that missions are managed externally |

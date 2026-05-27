# Performance Rules — Big O, N+1, Queries, Memory, Async

## Big O Analysis

Every non-trivial algorithm must be analysed before writing. Ask:
1. What is the input? (number of vehicles, events per second, query result size)
2. What does this scale to? (50 vehicles today; 500 at 10× scale)
3. Is there a hidden loop inside another loop?

### Reference for This Project

| Operation | Expected | Acceptable ceiling |
|-----------|----------|--------------------|
| Ingest single event | O(1) DB writes | — |
| Anomaly rule evaluation | O(k) where k = rule count (constant) | — |
| Fleet aggregate query | O(n) DB scan, O(1) result | — |
| Zone counts query | O(20) — fixed constant | — |
| Anomaly filter (vehicle + range) | O(log n) with index | O(n) without index is a bug |
| Vehicle list render (frontend) | O(50) — constant | — |

### Algorithm Classification

```
O(1)   — constant: dict lookup, DB point query by PK
O(log n) — logarithmic: indexed DB range scan
O(n)   — linear: full table scan, iterating all vehicles once
O(n log n) — sort: acceptable for small n
O(n²)  — quadratic: nested loops over vehicles/events — NEVER in hot paths
O(2^n) — exponential: recursion without memoisation on combinatorial input — NEVER
```

### Red Flags in This Codebase

```python
# O(n²) — iterating events inside a loop over vehicles
for vehicle in vehicles:
    for event in all_events:            # scans ALL events per vehicle
        if event.vehicle_id == vehicle.id:
            ...

# Fix: group first O(n), then iterate O(n) — total O(n)
from itertools import groupby
events_by_vehicle = {k: list(v) for k, v in groupby(sorted_events, key=lambda e: e.vehicle_id)}
```

---

## N+1 Query Detection

The N+1 problem: loading N parent records then issuing 1 query per parent = N+1 total queries.

### How to Spot N+1

```python
# N+1 — 1 query for vehicles, then N queries for anomalies
vehicles = await repo.get_all_vehicles()          # 1 query
for v in vehicles:
    anomalies = await repo.get_anomalies(v.id)    # N queries ← N+1
    v.latest_anomaly = anomalies[0] if anomalies else None
```

### Fix Patterns

**Option A — JOIN or subquery (best for DB)**:
```python
# One query with lateral join or subquery for latest anomaly per vehicle
query = (
    select(VehicleState, Anomaly)
    .outerjoin(
        Anomaly,
        and_(
            Anomaly.vehicle_id == VehicleState.vehicle_id,
            Anomaly.id == (
                select(func.max(Anomaly.id))
                .where(Anomaly.vehicle_id == VehicleState.vehicle_id)
                .scalar_subquery()
            )
        )
    )
)
```

**Option B — batch load then merge in Python (acceptable for small n)**:
```python
vehicles = await repo.get_all_vehicles()          # 1 query
vehicle_ids = [v.vehicle_id for v in vehicles]
anomalies = await repo.get_latest_anomalies_for(vehicle_ids)  # 1 batch query
anomaly_map = {a.vehicle_id: a for a in anomalies}
for v in vehicles:
    v.latest_anomaly = anomaly_map.get(v.vehicle_id)
```

### SQLAlchemy Async N+1 Traps

- **Lazy loading is disabled in async mode** — accessing `vehicle.missions` without `selectinload` raises `MissingGreenlet`. This is good: it forces explicit loading.
- Always use `selectinload` or `joinedload` when you need related objects:

```python
query = select(VehicleState).options(selectinload(VehicleState.missions))
```

- If you don't need the relationship, don't load it at all.

### N+1 in Frontend (React)

```typescript
// N+1 — one query per vehicle in VehicleList
function VehicleRow({ vehicleId }: { vehicleId: string }) {
  const { data: anomaly } = useQuery({   // N queries in parallel
    queryKey: ["anomaly", vehicleId],
    queryFn: () => getLatestAnomaly(vehicleId),
  });
}

// Fix — one query for all anomalies, filter in component
function VehicleList() {
  const { data: anomalies } = useQuery({   // 1 query
    queryKey: ["anomalies", "latest"],
    queryFn: getAllLatestAnomalies,
  });
  const anomalyMap = useMemo(
    () => Object.fromEntries(anomalies?.map(a => [a.vehicle_id, a]) ?? []),
    [anomalies]
  );
  return vehicles.map(v => <VehicleRow key={v.id} latestAnomaly={anomalyMap[v.vehicle_id]} />);
}
```

---

## Database Query Performance

### Index Usage

Verify your queries use indexes. Run `EXPLAIN ANALYZE` on all query shapes:

```sql
EXPLAIN ANALYZE
SELECT * FROM anomalies
WHERE vehicle_id = 'v-01' AND detected_at BETWEEN '2026-05-27' AND '2026-05-28';
-- Should show: Index Scan using idx_anomalies_vehicle_timestamp
-- Never: Seq Scan on large tables
```

**Required indexes for this project**:
```sql
CREATE INDEX idx_telemetry_vehicle_ts ON telemetry_events (vehicle_id, timestamp DESC);
CREATE INDEX idx_anomalies_vehicle_ts ON anomalies (vehicle_id, detected_at DESC);
```

### Query Anti-Patterns

```python
# NEVER — unbounded query
await session.execute(select(TelemetryEvent))  # returns ALL rows

# ALWAYS — paginate or limit
await session.execute(select(TelemetryEvent).limit(100).offset(offset))

# NEVER — SELECT * when only 3 fields needed
select(TelemetryEvent)  # loads all columns including large JSONB

# BETTER — select only needed columns
select(TelemetryEvent.vehicle_id, TelemetryEvent.status, TelemetryEvent.battery_pct)

# NEVER — count rows by loading them
total = len(await session.execute(select(TelemetryEvent)).scalars().all())

# CORRECT
total = await session.scalar(select(func.count()).select_from(TelemetryEvent))
```

### Pagination Pattern

```python
async def get_anomalies_paginated(
    vehicle_id: str | None,
    start: datetime | None,
    end: datetime | None,
    limit: int = 100,   # default
    offset: int = 0,
    session: AsyncSession,
) -> tuple[list[Anomaly], int]:
    base = select(Anomaly).order_by(Anomaly.detected_at.desc())
    if vehicle_id:
        base = base.where(Anomaly.vehicle_id == vehicle_id)
    # ... other filters

    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    rows = await session.execute(base.limit(min(limit, 500)).offset(offset))
    return rows.scalars().all(), total
```

---

## Memory Complexity

| Pattern | Memory | Notes |
|---------|--------|-------|
| `list(result.scalars().all())` | O(n) | Fine for n ≤ 500; bad for full table dumps |
| Streaming with async generator | O(1) per chunk | Required for large exports |
| Dict comprehension over all vehicles | O(50) | Constant — acceptable |
| Accumulating all telemetry in RAM | O(n × time) | Never do this |

### Streaming for Large Result Sets

```python
# If you ever need to return all telemetry (e.g., export endpoint):
async def stream_telemetry(session: AsyncSession) -> AsyncGenerator[TelemetryEvent, None]:
    result = await session.stream(select(TelemetryEvent).order_by(TelemetryEvent.timestamp))
    async for row in result:
        yield row
```

---

## Async Performance

### Connection Pool

```python
# asyncpg default pool: min=10, max=10
# 50 vehicles at 1 Hz = 50 concurrent requests — default pool is sufficient
# If you see connection timeout errors, tune:
engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
)
```

### Avoid Blocking the Event Loop

```python
# BLOCKS event loop — never in async code
import time
time.sleep(1)             # blocks
open("file.txt").read()   # blocks (use aiofiles if needed)
requests.get(url)         # blocks (use httpx.AsyncClient)

# Correct: offload CPU-heavy work
import asyncio
result = await asyncio.to_thread(cpu_heavy_function, data)
```

### Batch Writes

```python
# SLOW — one INSERT per event
for event in events:
    session.add(TelemetryEvent(**event.dict()))

# FAST — bulk insert
await session.execute(
    insert(TelemetryEvent),
    [event.model_dump() for event in events]
)
```

---

## Performance Checklist (Pre-merge)

- [ ] Every loop over a DB result set is bounded by `.limit()`
- [ ] No N+1 queries — verify with `echo=True` on engine in tests, count SQL statements
- [ ] All query filter columns have indexes; `EXPLAIN ANALYZE` confirms index scans
- [ ] No `time.sleep()`, `requests.get()`, or other sync-blocking calls in async code
- [ ] Algorithms on variable-size inputs are O(n) or better
- [ ] No nested loops where the inner loop scales with data size
- [ ] Memory usage for any single request is bounded (no accumulating all-time data in RAM)
- [ ] DB connection pool size documented and sized for expected concurrency

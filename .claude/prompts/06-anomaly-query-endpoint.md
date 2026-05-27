# Prompt 06 — Anomaly Query Endpoint

## Goal

Implement `GET /anomalies` with filtering by vehicle and time range.

## Endpoint

```
GET /anomalies?vehicle_id=v-01&start=2026-05-27T10:00:00Z&end=2026-05-27T11:00:00Z&limit=100
```

All query params optional:
- `vehicle_id`: filter by specific vehicle
- `start` / `end`: ISO 8601 datetime, filter `detected_at` range
- `limit`: default 100, max 500

**Response**:
```json
[
  {
    "id": 1,
    "vehicle_id": "v-01",
    "detected_at": "2026-05-27T10:05:00Z",
    "type": "low_battery",
    "detail": {"battery_pct": 12}
  }
]
```

## Repository Method

```python
async def get_anomalies(
    vehicle_id: str | None,
    start: datetime | None,
    end: datetime | None,
    limit: int,
    session: AsyncSession,
) -> list[Anomaly]:
    query = select(Anomaly).order_by(Anomaly.detected_at.desc()).limit(limit)
    if vehicle_id:
        query = query.where(Anomaly.vehicle_id == vehicle_id)
    if start:
        query = query.where(Anomaly.detected_at >= start)
    if end:
        query = query.where(Anomaly.detected_at <= end)
    result = await session.execute(query)
    return list(result.scalars().all())
```

## Tests to Write

1. `test_anomaly_query_no_filters_returns_all`
2. `test_anomaly_query_vehicle_filter`
3. `test_anomaly_query_time_range_filters_correctly`
4. `test_anomaly_query_outside_range_returns_empty`
5. `test_anomaly_query_limit_respected`

## Acceptance Criteria

- `(vehicle_id, detected_at)` index exists on anomalies table
- All filters applied correctly (verify with boundary values)
- Default limit prevents unbounded queries
- All 5 tests pass

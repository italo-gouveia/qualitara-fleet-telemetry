# Logging Rules

## Framework

- Use Python's standard `logging` module via `structlog` (preferred) or plain `logging` with JSON formatter.
- Configure in `app/main.py` lifespan; respect `LOG_LEVEL` env var.
- In tests: set level to `WARNING` to reduce noise.

## Levels

| Level | When |
|-------|------|
| `ERROR` | Unhandled exception, DB failure, data loss risk |
| `WARNING` | Anomaly detected, retried operation, degraded state |
| `INFO` | Request lifecycle (method, path, status, duration), startup config summary |
| `DEBUG` | SQL queries, step-by-step flow — **only behind `LOG_LEVEL=DEBUG`** |

## What to Log

```python
# Startup — summarise config without secrets
logger.info("Starting Fleet Monitor", db_url_host=settings.db_host, log_level=settings.log_level)

# Ingest — one line, not one per vehicle event field
logger.info("Telemetry ingested", vehicle_id=event.vehicle_id, status=event.status)

# Anomaly — always at WARNING
logger.warning("Anomaly detected", vehicle_id=event.vehicle_id, anomaly_type=anomaly.type)

# Fault transition
logger.warning("Fault transition: cancelling mission", vehicle_id=vehicle_id, mission_id=str(mission.id))
```

## What Never to Log

- `DATABASE_URL` (contains password)
- Full request/response bodies
- `lat`/`lon` if considered PII in your deployment context
- `error_codes` array at INFO level (can be voluminous) — use DEBUG
- Any field named `password`, `secret`, `token`, `key`

## Correlation / Request ID

- Generate a `request_id` (UUID) per incoming request in middleware; bind to log context.
- Include in all log lines for that request using `structlog.contextvars.bind_contextvars(request_id=rid)`.
- Return `X-Request-Id: <uuid>` in response header so client can correlate.

## Format

- **Development**: human-readable colored text (structlog default dev renderer).
- **Production**: JSON lines — one JSON object per log line, fields as keys.

```json
{"timestamp": "2026-05-27T14:00:00Z", "level": "warning", "event": "Anomaly detected", "vehicle_id": "v-12", "anomaly_type": "low_battery", "request_id": "abc-123"}
```

## Anti-Patterns

```python
# WRONG — string concat, logs inside loops
for event in events:
    logger.info("Processing event: " + str(event))  # O(n) logs, concatenation

# CORRECT — batch summary
logger.info("Batch ingested", count=len(events))
```

# Prompt 15 — Observability: Structured Logging

## Context

Peer review flagged absence of structured logging throughout the application.
The description says "production-grade async Python" — production-grade means every
request, business event, and failure is observable from logs alone.

Currently:
- `logging.basicConfig(level=settings.log_level.upper())` in `main.py` — plain text, no context
- Services have zero log calls
- Exception handler logs method + path but no request correlation
- Docker compose has `LOG_LEVEL=INFO` but no structured format setting

## Goal

Add structured, contextual logging across the stack so an operator can trace any
telemetry event, fault transition, or anomaly from a single log line without reading
the database.

---

## Deliverables

### 1. `python-json-logger` dependency

Add `python-json-logger>=3.2` to `backend/requirements.txt`.

### 2. `LOG_FORMAT` setting in `config.py`

Add `log_format: str = "json"` to `Settings`.  
`json` → machine-readable JSON output (production/Docker).  
`text` → human-readable plain text (local dev override via `.env`).

### 3. `backend/app/core/logging_config.py`

`setup_logging(level: str, fmt: str) -> None` — configure the root logger once:
- `fmt="json"` → `JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")`
- `fmt="text"` → `logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")`
- Replace `logging.basicConfig` call in `main.py` with `setup_logging(settings.log_level, settings.log_format)`.

### 4. `backend/app/middleware/request_logging.py`

`RequestLoggingMiddleware(BaseHTTPMiddleware)`:
- Read `X-Request-Id` header; generate `str(uuid.uuid4())` if absent.
- Call `call_next(request)` and measure wall-clock duration.
- After response: `logger.info("http_request", extra={...})` with keys:
  `request_id`, `method`, `path`, `status_code`, `duration_ms`.
- Set `X-Request-Id` on response headers so clients can correlate.

Add to `app` in `main.py` **before** the existing `CORSMiddleware`:
```python
app.add_middleware(RequestLoggingMiddleware)
```
(Starlette processes middleware in reverse-add order, so request_logging wraps cors.)

### 5. Structured business-event logs in services

**`app/services/telemetry.py`** — after side-effects are written, before return:
```python
logger.info(
    "telemetry_ingested",
    extra={
        "vehicle_id": event.vehicle_id,
        "status": event.status,
        "battery_pct": event.battery_pct,
        "zone_entered": event.zone_entered,
        "anomalies_detected": len(detected),
        "event_id": str(event_id),
    },
)
```

**`app/services/vehicle.py`** — in `update_vehicle_status`, after mutation, before return:
```python
logger.info(
    "vehicle_status_updated",
    extra={
        "vehicle_id": vehicle_id,
        "new_status": new_status.value,
        "mission_cancelled": result.mission_cancelled,
    },
)
```

**`app/core/anomaly.py`** — not required (logged indirectly via telemetry service log).

### 6. Update `exception_handlers.py`

Add `request_id` from `request.headers.get("X-Request-Id", "unknown")` to the
ERROR log call so 500s are traceable.

### 7. Update `docker-compose.yml`

Add `LOG_FORMAT: json` to the backend `environment` block.

---

## What NOT to do

- Do not add Prometheus metrics or distributed tracing (separate prompt if needed).
- Do not log full request/response bodies (security: may contain sensitive data).
- Do not log the `DATABASE_URL` or any credential at any level.

---

## Acceptance criteria

- [ ] `python-json-logger` in requirements.txt
- [ ] `log_format` setting in `config.py`
- [ ] `setup_logging()` in `logging_config.py`, called from `main.py`
- [ ] `RequestLoggingMiddleware` exists; every response includes `X-Request-Id` header
- [ ] `telemetry_ingested` log line with `vehicle_id`, `battery_pct`, `anomalies_detected`
- [ ] `vehicle_status_updated` log line with `vehicle_id`, `new_status`, `mission_cancelled`
- [ ] Exception handler includes `request_id` in ERROR log
- [ ] `LOG_FORMAT: json` in docker-compose backend env
- [ ] `pytest -v` 24 passed
- [ ] `ruff check .` / `mypy app/` clean

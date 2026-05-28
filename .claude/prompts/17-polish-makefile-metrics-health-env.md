# Prompt 17 — Final Polish: Makefile, Prometheus, Health DB Check, .env.example, Tests

## Context

Seven gaps remain before submission:
1. README API table missing `GET /vehicles/{vehicle_id}` (added Prompt 16).
2. No `.env.example` — devs cloning the repo don't know what vars to set.
3. No `Makefile` — no single command to test, lint, or start the stack.
4. `GET /health` returns `{"status": "ok"}` without verifying DB connectivity.
5. No Prometheus metrics endpoint — peer review flagged missing observability tooling.
6. No test for the exception handler (500 response shape).
7. No test for `X-Request-Id` header propagation.

---

## Deliverable 1 — README API table update

Add `GET /vehicles/{vehicle_id}` row. Add pagination note to `GET /vehicles`.
Add `/metrics` row for Prometheus.

---

## Deliverable 2 — `backend/.env.example`

```
DATABASE_URL=postgresql+asyncpg://fleet:fleet@localhost:5432/fleet
LOG_LEVEL=INFO
LOG_FORMAT=text
CORS_ORIGINS=["http://localhost:5173"]
```

Comment: `LOG_FORMAT=text` for human-readable dev output; set to `json` in production.

---

## Deliverable 3 — `Makefile` at repo root

Targets:
- `make test` — `cd backend && python -m pytest tests/ -v`
- `make lint` — ruff + mypy in backend
- `make up` — `docker compose up --build`
- `make down` — `docker compose down`
- `make dev` — `cd backend && fastapi dev app/main.py`
- `make help` — list available targets (default target)

---

## Deliverable 4 — `GET /health` with DB readiness check

Replace the current stub with a real check:
- Inject `SessionDep`; execute `SELECT 1`.
- On success → 200 `{"status": "ok"}`.
- On `Exception` → log `WARNING health_check_db_unavailable`, set `response.status_code = 503`,
  return `{"status": "unavailable"}`.

This makes the docker-compose `healthcheck: curl -f http://localhost:8000/health`
meaningful — it will fail if the DB is unreachable.

Import `Response` from fastapi; import `text` from sqlalchemy (already imported in main.py).

---

## Deliverable 5 — Prometheus metrics

Add `prometheus-fastapi-instrumentator>=0.9` to `requirements.txt`.

In `main.py`, after the app and routers are wired:
```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

This exposes `GET /metrics` with:
- `http_requests_total` (method, handler, status)
- `http_request_duration_seconds` (latency histogram)

Add `/metrics` to README API table.

---

## Deliverable 6 — Missing tests

File: `backend/tests/integration/test_observability.py`

### Exception handler test

Patch `app.services.fleet.get_fleet_state` with `AsyncMock(side_effect=RuntimeError("boom"))`,
call `GET /fleet/state`, assert:
- status 500
- `response.json()["detail"] == "An unexpected error occurred. Please try again later."`

### X-Request-Id tests

- Any response includes `x-request-id` header (call `GET /health`).
- If `X-Request-Id: my-id` is sent, the same value is echoed back.

### Prometheus smoke test

`GET /metrics` → 200, body contains `http_requests_total`.

### Health DB check test

`GET /health` → 200 with `{"status": "ok"}` (normal path, DB is up in tests).

---

## Acceptance criteria

- [ ] README has `GET /vehicles/{vehicle_id}` and `/metrics` in API table
- [ ] `backend/.env.example` exists with all 4 settings
- [ ] `Makefile` at repo root with 6 targets
- [ ] `GET /health` executes `SELECT 1` and returns 503 on failure
- [ ] `GET /metrics` returns 200 with Prometheus text format
- [ ] `test_observability.py` has 5 tests (500 shape, request-id present, request-id echoed, metrics 200, health 200)
- [ ] `pytest -v` all green
- [ ] `ruff check .` / `mypy app/` clean

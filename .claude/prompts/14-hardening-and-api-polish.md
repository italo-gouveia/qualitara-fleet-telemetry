# Prompt 14 — Hardening & API Polish

## Goal

Five targeted improvements before submission:
1. Global exception handler — clean 500s, no raw SQLAlchemy leaks
2. FastAPI entrypoint in `pyproject.toml` — follow our own skill
3. `vehicle_id` input validation — max length on body, path and query params
4. OpenAPI descriptions on key endpoints — Swagger UI tells the story
5. `GET /vehicles` pagination — `limit` + `offset` query params

---

## 1. Global Exception Handler

### File: `app/core/exception_handlers.py` (new)

```python
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method, request.url.path, exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )
```

### Wire in `app/main.py`

```python
from app.core.exception_handlers import unhandled_exception_handler
...
app.add_exception_handler(Exception, unhandled_exception_handler)
```

Place **after** `add_middleware`, **before** `include_router` calls.

---

## 2. FastAPI Entrypoint in `pyproject.toml`

```toml
[tool.fastapi]
entrypoint = "app.main:app"
```

After this, `fastapi dev` (no path argument) works from the `backend/` directory.
Update README local-dev command accordingly.

---

## 3. `vehicle_id` Input Validation

### `app/schemas/telemetry.py`

```python
vehicle_id: Annotated[str, Field(min_length=1, max_length=20)]
```

### `app/routers/vehicle.py`

Add `Path()` validation on the path parameter:

```python
from fastapi import Path
...
vehicle_id: Annotated[str, Path(min_length=1, max_length=20)],
```

### `app/routers/anomaly.py`

```python
vehicle_id: Annotated[str | None, Query(max_length=20)] = None,
```

---

## 4. OpenAPI Descriptions

### `app/main.py` — enrich the FastAPI app metadata

```python
app = FastAPI(
    title="Fleet Telemetry Monitor",
    description=(
        "Real-time monitoring API for 50 autonomous industrial vehicles.\n\n"
        "Ingest telemetry at 1 Hz, track vehicle states, zone entry counts, "
        "and anomaly events. See `docs/ADR.md` for architecture decisions."
    ),
    version="0.1.0",
    lifespan=lifespan,
)
```

### Add `summary` to the critical endpoints

- `POST /telemetry` — `summary="Ingest a telemetry event"`
- `GET /fleet/state` — `summary="Per-status vehicle counts"`
- `GET /vehicles` — `summary="All known vehicles, paginated"`
- `PATCH /vehicles/{vehicle_id}/status` — `summary="Update vehicle status; fault cancels active mission"`
- `GET /anomalies` — `summary="Query anomaly events with optional filters"`

---

## 5. `GET /vehicles` Pagination

### `app/repositories/vehicle_repository.py`

Add `limit` and `offset` parameters:

```python
async def get_all_vehicle_states(
    session: AsyncSession, limit: int = 50, offset: int = 0
) -> list[VehicleStateResponse]:
    rows = await session.execute(
        select(VehicleState)
        .order_by(VehicleState.vehicle_id)
        .limit(limit)
        .offset(offset)
    )
    ...
```

### `app/services/fleet.py`

Pass through `limit` and `offset`:

```python
async def get_vehicles(
    session: AsyncSession, limit: int = 50, offset: int = 0
) -> list[VehicleStateResponse]:
    return await get_all_vehicle_states(session, limit=limit, offset=offset)
```

### `app/routers/fleet.py`

```python
@router.get("/vehicles", response_model=list[VehicleStateResponse])
async def vehicles(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[VehicleStateResponse]:
    return await get_vehicles(session, limit=limit, offset=offset)
```

Default `limit=50` preserves backward compatibility (current fleet size).

---

## Tests to update

- `test_fleet_endpoints.py` — pagination tests already pass `limit=50` default implicitly;
  add one explicit test: `GET /vehicles?limit=1&offset=0` returns exactly 1 vehicle.

---

## Acceptance Criteria

- [ ] Unhandled DB/runtime errors return `{"detail": "An unexpected error occurred..."}` with 500
- [ ] `fastapi dev` works from `backend/` with no path argument
- [ ] `POST /telemetry` with `vehicle_id` > 20 chars returns 422
- [ ] `GET /vehicles?limit=1` returns exactly 1 vehicle
- [ ] Swagger UI at `/docs` shows descriptions on all key endpoints
- [ ] `pytest -v` — all tests pass (add pagination test)
- [ ] `ruff check .` and `mypy app/` clean
- [ ] Add Interaction 14 to `docs/AI_INTERACTION_LOG.md`

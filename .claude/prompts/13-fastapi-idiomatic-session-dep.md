# Prompt 13 — FastAPI Idiomatic: SessionDep Alias

## Motivation

The official FastAPI skill (`fastapi/fastapi/.agents/skills/fastapi/SKILL.md`) recommends
using `Annotated` style for all dependency declarations, creating reusable type aliases
rather than repeating the full `Depends()` expression in every handler signature.

Currently all five routers repeat:

```python
session: AsyncSession = Depends(get_session)
```

The idiomatic FastAPI pattern is a single alias used everywhere:

```python
# database.py (or deps.py)
SessionDep = Annotated[AsyncSession, Depends(get_session)]

# any router
async def my_handler(session: SessionDep) -> ...:
```

The skill also recommends `fastapi dev` (FastAPI CLI) over `uvicorn --reload` for local
development — it ships with `fastapi>=0.115` which is already in our requirements.

---

## Changes

### 1. Add `SessionDep` to `app/database.py`

```python
from typing import Annotated
from fastapi import Depends

SessionDep = Annotated[AsyncSession, Depends(get_session)]
```

### 2. Update all five routers

Replace every `session: AsyncSession = Depends(get_session)` parameter with
`session: SessionDep`. Remove the now-unused `AsyncSession` and `Depends` imports
from each router file (if not used elsewhere).

Routers to update:
- `app/routers/telemetry.py`
- `app/routers/fleet.py`
- `app/routers/vehicle.py`
- `app/routers/anomaly.py`

(telemetry service also receives session — router passes it through, so only
the router signature changes.)

### 3. Update README local-dev command

```bash
# Before
uvicorn app.main:app --reload

# After
fastapi dev app/main.py
```

---

## Acceptance Criteria

- [ ] `SessionDep` defined in `app/database.py`
- [ ] All router handler signatures use `session: SessionDep`
- [ ] No router imports `Depends` or `AsyncSession` solely for the session dep
- [ ] `pytest -v` — 23 passed
- [ ] `ruff check .` and `mypy app/` clean
- [ ] README local-dev command updated to `fastapi dev app/main.py`
- [ ] Add Interaction 13 to `docs/AI_INTERACTION_LOG.md`

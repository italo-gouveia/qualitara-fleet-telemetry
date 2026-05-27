# Prompt 01 — Project Bootstrap

## Goal

Create the complete scaffolding for the backend and frontend so all subsequent prompts can build on a working skeleton.

## Context to Read

- `.claude/context/challenge-spec.md`
- `.claude/context/tech-decisions.md`
- `.claude/rules/simplicity-first.md`

## What to Create

### Backend (`backend/`)

```
backend/
├── pyproject.toml          # or requirements.txt
├── alembic.ini
├── alembic/
│   └── versions/           # empty initially
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI app, lifespan, CORS
│   ├── config.py           # pydantic-settings BaseSettings
│   ├── database.py         # engine, async session factory, Base
│   ├── models/
│   │   └── __init__.py
│   ├── schemas/
│   │   └── __init__.py
│   ├── routers/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   ├── repositories/
│   │   └── __init__.py
│   └── core/
│       ├── zones.py        # ZONES constant (20 zones)
│       └── anomaly.py      # empty anomaly rule list
└── tests/
    ├── conftest.py
    ├── helpers.py          # make_event() factory
    ├── unit/
    │   └── __init__.py
    └── integration/
        └── __init__.py
```

### Frontend (`frontend/`)

Use: `npm create vite@latest frontend -- --template react-ts`
Then install: `@tanstack/react-query`

### Files to Produce

**`backend/app/config.py`**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./fleet.db"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"

settings = Settings()
```

**`backend/app/database.py`**: async engine, `AsyncSessionLocal`, `Base`, `get_session` dependency.

**`backend/app/main.py`**: FastAPI app with CORS middleware, lifespan that calls `create_all`, includes router stubs.

**`backend/app/core/zones.py`**: `ZONES` list (20 zones from spec).

**`.env.example`**: `DATABASE_URL=`, `LOG_LEVEL=INFO`, `CORS_ORIGINS=http://localhost:5173`

**`backend/tests/conftest.py`**: full fixture setup per `.claude/rules/integration-testing-guide.md`.

**`backend/tests/helpers.py`**: `make_event(**overrides)` returning a valid telemetry dict.

## Acceptance Criteria

- `cd backend && uvicorn app.main:app --reload` starts without error
- `GET http://localhost:8000/docs` returns Swagger UI
- `cd backend && pytest` runs (0 tests, no errors)
- `cd frontend && npm run dev` starts without error

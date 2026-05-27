# Prompt 10 — Final Review and Submission Prep

## Goal

Run the code reviewer agent checklist, fix any failures, write the README, and prepare for GitHub submission.

## Agent

Use: `.claude/agents/code-reviewer.agent.md` — run through every item in the checklist.

## README.md Requirements

```markdown
# Fleet Telemetry Monitor

Real-time monitoring for 50 autonomous industrial vehicles.

## Stack
- Backend: Python 3.12, FastAPI, SQLAlchemy async, PostgreSQL/SQLite
- Frontend: React 18, TypeScript, Vite, TanStack Query

## How to Run

### Backend

\```bash
cd backend
cp ../.env.example .env   # edit DATABASE_URL if using Postgres
pip install -e ".[dev]"   # or: uv sync
alembic upgrade head
uvicorn app.main:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
\```

### Frontend

\```bash
cd frontend
npm install
npm run dev
# Dashboard: http://localhost:5173
\```

### Simulate Fleet (optional)

\```bash
python backend/scripts/simulate_fleet.py
\```

### Run Tests

\```bash
cd backend
pytest -v
ruff check .
mypy .
\```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | sqlite+aiosqlite:///./fleet.db | DB connection string |
| LOG_LEVEL | INFO | Logging level |
| CORS_ORIGINS | http://localhost:5173 | Allowed frontend origin |

## Architecture

See [docs/ADR.md](docs/ADR.md) for design decisions.

## AI Usage

This project was built with Claude Code (Anthropic). See [docs/AI_INTERACTION_LOG.md](docs/AI_INTERACTION_LOG.md) for a full log of AI interactions and corrections.
```

## Pre-Submission Checklist

```bash
# All tests pass
cd backend && pytest -v

# Linting passes
ruff check . && mypy .

# Frontend builds
cd frontend && npm run build

# No secrets in repo
git log --all -- .env
git grep "password\|secret\|privatekey" -- '*.py' '*.ts'

# .local-context is gitignored
git check-ignore -v .local-context/

# All deliverables exist
ls docs/ADR.md docs/AI_INTERACTION_LOG.md README.md
```

## GitHub Push

```bash
git add -A
git status  # review staged files — no .env, no .db
git commit -m "feat: complete fleet telemetry monitoring service"
git push origin main
```

Reply to Jacki's email with the public repo link.

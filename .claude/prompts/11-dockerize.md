# Prompt 11 — Dockerize the Full Stack (PostgreSQL)

## Goal

Containerize the application with Docker Compose so the full stack (PostgreSQL, FastAPI backend, React dashboard) can be started with a single command. Replace the SQLite default with PostgreSQL for the running application. Tests must continue to use in-memory SQLite — do not touch `conftest.py`.

## Agent

Use: `.claude/agents/senior-python-developer.agent.md`

## Files to Create

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Orchestrates `db`, `backend`, `frontend` services |
| `backend/Dockerfile` | `python:3.12-slim`; layer-cached deps; delegates to `entrypoint.sh` |
| `backend/entrypoint.sh` | `alembic upgrade head` then `uvicorn` |
| `backend/.dockerignore` | Excludes `fleet.db`, `.env`, caches |
| `frontend/Dockerfile` | Multi-stage: `node:20-alpine` build → `nginx:alpine` serve |
| `frontend/nginx.conf` | SPA `try_files` fallback; gzip |
| `frontend/.dockerignore` | Excludes `node_modules`, `dist`, `.env` |

## docker-compose.yml Requirements

```yaml
services:
  db:
    image: postgres:16-alpine
    # env: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD all = fleet
    # healthcheck: pg_isready -U fleet -d fleet (interval 5s, retries 10)
    # volume: pgdata
    # ports: 5432:5432

  backend:
    build: { context: backend }
    # env: DATABASE_URL=postgresql+asyncpg://fleet:fleet@db:5432/fleet
    # depends_on: db (condition: service_healthy)
    # ports: 8000:8000

  frontend:
    build:
      context: frontend
      args:
        VITE_API_BASE_URL: http://localhost:8000  # baked at build time
    # depends_on: backend
    # ports: 5173:80

volumes:
  pgdata:
```

## backend/entrypoint.sh

```sh
#!/bin/sh
set -e
echo "Running database migrations..."
alembic upgrade head
echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## frontend/Dockerfile (multi-stage)

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

## frontend/nginx.conf

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    gzip on;
    gzip_types text/plain text/css application/javascript application/json;
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## Design Constraints

- **PostgreSQL in Docker, SQLite for tests**: `conftest.py` creates its own in-memory SQLite engine, independent of `app.config.settings`. Do not change it.
- **Zone seeding**: `main.py` `lifespan` already calls `_seed_zone_counts()` with `ON CONFLICT DO NOTHING` — no new Alembic migration needed.
- **`VITE_API_BASE_URL`**: Vite bakes `import.meta.env.VITE_*` at bundle time. The value `http://localhost:8000` is correct for local Docker usage. To access from a remote machine, rebuild with `--build-arg VITE_API_BASE_URL=http://<host-ip>:8000`.
- **`dialect_insert()`** in `database.py` already branches on `engine.dialect.name` — correct dialect is picked automatically when connected to PostgreSQL.

## Files to Update

- `backend/.env.example` — add PostgreSQL comment; fix `CORS_ORIGINS` to JSON array format
- `frontend/.env.example` — clarify Docker vs local-dev
- `README.md` — add "Quick Start with Docker Compose" section before the manual setup instructions
- `docs/AI_INTERACTION_LOG.md` — add Interaction 11

## Acceptance Criteria

- [ ] `docker compose up --build` starts all three services cleanly
- [ ] Backend only starts after `pg_isready` passes (`service_healthy`)
- [ ] `alembic upgrade head` runs automatically before uvicorn starts
- [ ] Dashboard accessible at http://localhost:5173
- [ ] API and Swagger UI accessible at http://localhost:8000/docs
- [ ] `pytest -v` (local, SQLite) still passes — 23 tests, no changes to test files
- [ ] `docker compose down -v` removes the pgdata volume cleanly

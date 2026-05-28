.PHONY: help \
        test test-frontend test-e2e lint \
        up up-detached down reset logs ps \
        dev migrate simulate \
        load-test

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Testing ───────────────────────────────────────────────────────────────────

test: ## Run backend tests (pytest -v)
	cd backend && python -m pytest tests/ -v

test-frontend: ## Run frontend unit + integration tests (Vitest)
	cd frontend && npm test

test-e2e: ## Run Playwright E2E tests (Chromium; stack must be running)
	cd frontend && npm run test:e2e

lint: ## Lint + type-check backend (ruff + mypy)
	cd backend && python -m ruff check app/ tests/ && python -m mypy app/ --ignore-missing-imports

# ── Stack ─────────────────────────────────────────────────────────────────────

up: ## Build and start the full stack (DB + backend + frontend + Prometheus + Grafana)
	docker compose up --build

up-detached: ## Start the full stack in the background (-d)
	docker compose up --build -d

down: ## Stop containers (data preserved)
	docker compose down

reset: ## Full reset: wipe DB volume, rebuild, and start fresh
	docker compose down -v && docker compose up --build

logs: ## Tail logs from all services (Ctrl+C to stop)
	docker compose logs -f

ps: ## Show running service status
	docker compose ps

# ── Local development ─────────────────────────────────────────────────────────

dev: ## Start backend in dev/hot-reload mode (SQLite)
	cd backend && fastapi dev app/main.py

migrate: ## Apply Alembic migrations locally (SQLite)
	cd backend && alembic upgrade head

simulate: ## Send 50-vehicle telemetry at 1 Hz against localhost:8000
	python backend/scripts/simulate_fleet.py

# ── Load testing ──────────────────────────────────────────────────────────────

load-test: ## Full stack + Locust UI (http://localhost:8089)
	docker compose --profile load-test up --build

.PHONY: help test lint up down dev load-test

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

test: ## Run the full test suite
	cd backend && python -m pytest tests/ -v

lint: ## Run ruff + mypy in backend
	cd backend && python -m ruff check app/ tests/ && python -m mypy app/ --ignore-missing-imports

up: ## Build and start the full stack (PostgreSQL + backend + frontend + Prometheus + Grafana)
	docker compose up --build

down: ## Stop and remove containers
	docker compose down

dev: ## Start the backend in dev mode (hot-reload, SQLite)
	cd backend && fastapi dev app/main.py

load-test: ## Full stack + Locust load tester (http://localhost:8089)
	docker compose --profile load-test up --build

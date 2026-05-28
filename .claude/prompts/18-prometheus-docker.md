# Prompt 18 — Prometheus (and Grafana) in Docker Compose

## Context

The backend already exposes GET /metrics via prometheus-fastapi-instrumentator.
But there is no Prometheus server in the stack to scrape it — metrics are exposed
but invisible. A recruiter doing `docker compose up --build` sees nothing in practice.

## Goal

Add Prometheus (and Grafana) as services in docker-compose.yml so the full
observability stack runs with a single command.

---

## Deliverables

### 1. `prometheus/prometheus.yml`

Scrape config pointing at the backend container:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: fleet-backend
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /metrics
```

### 2. `docker-compose.yml` — add prometheus and grafana services

```yaml
prometheus:
  image: prom/prometheus:v2.52.0
  volumes:
    - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
  ports:
    - "9090:9090"
  depends_on:
    backend:
      condition: service_healthy

grafana:
  image: grafana/grafana:10.4.3
  ports:
    - "3000:3000"
  environment:
    GF_SECURITY_ADMIN_USER: admin
    GF_SECURITY_ADMIN_PASSWORD: admin
    GF_AUTH_ANONYMOUS_ENABLED: "true"
    GF_AUTH_ANONYMOUS_ORG_ROLE: Viewer
  depends_on:
    - prometheus
```

Grafana anonymous viewer access so the recruiter can open it without logging in.
Admin password `admin` is fine for a local dev/demo stack (document it).

### 3. README — update Quick Start section

Add the new URLs to the "Stack is up" table:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin) |

Add a note that Grafana anonymous viewers can browse without login; to add a
dashboard: Connections → Add data source → Prometheus → URL `http://prometheus:9090`.

### 4. Makefile — no changes needed

`make up` already runs `docker compose up --build`.

---

## Acceptance criteria

- [ ] `prometheus/prometheus.yml` exists with correct scrape config
- [ ] `docker-compose.yml` has `prometheus` and `grafana` services
- [ ] `prometheus` depends on backend `service_healthy`
- [ ] README Quick Start table shows all 5 URLs
- [ ] `pytest -v` still passes (no app code changed)
- [ ] `ruff / mypy` still clean

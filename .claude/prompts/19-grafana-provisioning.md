# Prompt 19 — Grafana Provisioning (auto datasource + dashboard)

## Context

Grafana starts empty. The user has to manually add the Prometheus datasource
and create panels — that breaks the "single docker compose up" demo story.

Grafana supports file-based provisioning: YAML files for datasources and
dashboard providers, plus a JSON file for the dashboard itself. These are
mounted read-only at startup and Grafana applies them automatically.

## Goal

When `docker compose up --build` finishes, opening http://localhost:3000
shows a ready-to-use **Fleet Telemetry** dashboard — no manual steps needed.

---

## Deliverables

### Directory structure

```
grafana/
  provisioning/
    datasources/
      prometheus.yml     ← auto-register Prometheus as default datasource
    dashboards/
      provider.yml       ← tell Grafana where to find dashboard JSON files
      fleet.json         ← the actual dashboard
```

### `grafana/provisioning/datasources/prometheus.yml`

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    access: proxy
    isDefault: true
    editable: false
```

### `grafana/provisioning/dashboards/provider.yml`

```yaml
apiVersion: 1
providers:
  - name: Fleet Telemetry
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
```

### `grafana/provisioning/dashboards/fleet.json`

A Grafana dashboard JSON with 4 panels targeting
`prometheus-fastapi-instrumentator` metrics:

| Panel | Query | Type |
|-------|-------|------|
| Request Rate | `sum(rate(http_requests_total[1m])) by (handler, method)` | Time series |
| P95 Latency | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[1m])) by (le, handler))` | Time series |
| Error Rate (5xx) | `sum(rate(http_requests_total{status=~"5.."}[1m]))` | Stat |
| Requests by Status | `sum by (status) (increase(http_requests_total[5m]))` | Bar gauge |

Dashboard settings: `refresh: 10s`, time range last 15 minutes, uid `fleet-telemetry`.

### `docker-compose.yml` — mount provisioning into Grafana

```yaml
grafana:
  volumes:
    - ./grafana/provisioning:/etc/grafana/provisioning:ro
```

---

## Acceptance criteria

- [ ] `grafana/provisioning/datasources/prometheus.yml` exists
- [ ] `grafana/provisioning/dashboards/provider.yml` exists
- [ ] `grafana/provisioning/dashboards/fleet.json` is valid Grafana dashboard JSON
- [ ] `docker-compose.yml` grafana service mounts `./grafana/provisioning`
- [ ] Opening http://localhost:3000 shows Fleet Telemetry dashboard without login
- [ ] `pytest -v` still passes (no app code changed)

# Prompt 23 — README refresh, Vitest frontend tests, CHANGELOG

## Context

Three parallel gaps:

1. **README** is stale in several places: stack table missing new tools, API endpoint
   table missing /missions and /maintenance, architecture diagram doesn't show the
   observability stack, scalability roadmap doesn't mention Background Tasks as
   stepping stone, non-goals don't list deferred items.

2. **Frontend has zero tests.** Code review flagged this. All business logic lives in
   components and hooks; Vitest + Testing Library covers the key render contracts
   without touching the network.

3. **No CHANGELOG.md.** The git-handover rules recommend one; 22 prompts of work
   deserve a human-readable summary.

---

## Deliverables

### 1. README refresh

- Architecture diagram: add Prometheus/Grafana scrape loop below PostgreSQL
- Stack table: add python-json-logger, prometheus-fastapi-instrumentator, Locust, GitHub Actions
- API Endpoints table: add GET /vehicles/{id}/missions and GET /vehicles/{id}/maintenance
- Scalability Roadmap: add Background Tasks as stepping stone before Kafka row
- Non-Goals: add TestContainers (deferred), Alertmanager (deferred), Background Tasks→Kafka (roadmap)

### 2. Vitest — frontend tests

Install dev deps:
```
vitest @vitest/coverage-v8 @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

Add to `vite.config.ts`:
```ts
test: {
  globals: true,
  environment: 'jsdom',
  setupFiles: ['./src/test/setup.ts'],
}
```

Add scripts to `package.json`:
```json
"test": "vitest run",
"test:watch": "vitest"
```

**`src/test/setup.ts`** — import `@testing-library/jest-dom`

**Test files (mock hooks at module level with `vi.mock`):**

`FleetSummary.test.tsx` (3 tests):
- renders loading state when isLoading=true
- renders 4 status tiles with correct counts
- renders total vehicle count in heading

`ZoneCountsPanel.test.tsx` (3 tests):
- renders all zone rows
- sorts zones descending by count
- applies highlight class to zones with count > 10

`VehicleRow.test.tsx` (3 tests):
- renders vehicle ID and status badge
- shows battery percentage
- shows fault CSS class on row when status is fault

### 3. Update CI to run frontend tests

Add step to frontend job in `.github/workflows/ci.yml`:
```yaml
- name: Test
  run: npm test
```
(before or after Build step)

### 4. CHANGELOG.md

Keep a Changelog format. One `[Unreleased]` section grouping all work by category.

---

## Acceptance criteria

- [ ] README: diagram, stack, endpoints, roadmap, non-goals all updated
- [ ] Vitest installed and configured
- [ ] 9 frontend tests passing (`npm test`)
- [ ] CI workflow includes `npm test` step
- [ ] CHANGELOG.md present at repo root
- [ ] `pytest -v` still passes (no backend code changed)

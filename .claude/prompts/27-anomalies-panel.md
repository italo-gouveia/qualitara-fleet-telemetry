# Prompt 27 — Anomalies Panel: Dashboard Section + Full Test Coverage

## Goal

Add a dedicated **AnomaliesPanel** section to the React dashboard showing the most recent fleet-wide anomalies in real time. The `GET /anomalies` endpoint and `useVehicleAnomalies` hook already exist; the dashboard only shows a per-vehicle badge in `VehicleRow`. This prompt promotes anomalies to a full-width panel and adds unit, integration (MSW), and E2E (Playwright) coverage.

## Implementation

### `src/hooks/useAnomalies.ts` (new)
Fleet-wide hook — no `vehicleId` parameter, polls every 5 s, `queryKey: ["anomalies"]`.

### `src/components/AnomaliesPanel.tsx` (new)
Full-width panel below the vehicles/zones grid:
- Columns: **Vehicle** (monospace) | **Type** (badge) | **Detected** (relative time: "30s ago", "2m ago", "1h ago")
- Badge colour map: `critical_battery` / `fault_entered` → `badge-red`; `low_battery` / `speed_anomaly` / `error_code_reported` → `badge-orange`; unknown → `badge-slate`
- Count badge in heading: `<span class="panel-count">N</span>` — hidden when empty
- Empty state: `<p class="anomaly-empty">No anomalies detected.</p>`
- Loading / error states consistent with other panels

### `src/api/anomalies.ts` (update)
Change fleet-wide `limit` from `"50"` to `"20"` — keeps the panel focused on recent events.

### `src/App.tsx` (update)
Import `AnomaliesPanel`; add `<AnomaliesPanel />` after the `<div className="panels">` grid.

### `src/App.css` (update)
Add styles:
- `.panel-count` — small pill badge in panel headings
- `.anomaly-table` — same collapse/border pattern as `vehicle-table` and `zone-table`
- `.anomaly-vehicle` — monospace, muted colour
- `.anomaly-empty` — muted italic empty-state text

### `frontend/Dockerfile` (fix)
`COPY package*.json .npmrc ./` — `.npmrc` must be present before `npm ci` so `legacy-peer-deps=true` is active inside the container (same npm 10.x vs 11.x peer-dep issue that affected CI).

## Tests

### Unit — `src/test/AnomaliesPanel.test.tsx` (new, 6 tests)
Mock `useAnomalies` at module level (`vi.mock`):
1. Loading state renders "Loading anomalies…"
2. Error state renders `.error` element
3. Empty state renders "No anomalies detected."
4. Populated: vehicle IDs and human-readable type labels present
5. Count badge `.panel-count` shows correct number
6. `critical_battery` badge has class `badge-red`

### MSW handlers — `src/test/mocks/handlers.ts` (update)
Replace `HttpResponse.json([])` for `/anomalies` with 3 realistic anomaly objects (fault_entered, low_battery, critical_battery) so integration and E2E tests have non-trivial data.

### Integration — `Dashboard.integration.test.tsx` (4 new tests)
`AnomaliesPanel (integration)` describe block using real QueryClient + MSW:
1. loading → rows from API (vehicle IDs + type labels)
2. count badge equals number of anomalies returned
3. empty state when handler overridden to return `[]`
4. error state when handler overridden to return 500

### E2E — `e2e/fleet-dashboard.spec.ts` (4 new scenarios)
Add `ANOMALIES` fixture; override `beforeEach`'s `anomalies**` → `[]` route per-test where needed:
1. Empty state "No anomalies detected." visible (beforeEach already returns `[]`)
2. Heading + count badge visible when anomalies present
3. Vehicle IDs and `fault entered` / `low battery` labels rendered in table
4. `.badge-red` on first fault anomaly

## Acceptance criteria

- [ ] `npm test` → **39 passed** (unit + integration)
- [ ] `npm run test:e2e` → **11 passed**
- [ ] `npm run build` → clean (no TypeScript errors)
- [ ] `docker compose build` → frontend image builds successfully with `.npmrc` in place
- [ ] AnomaliesPanel visible in the running dashboard at http://localhost:5173

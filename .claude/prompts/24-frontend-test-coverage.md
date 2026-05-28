# Prompt 24 — Complete Frontend Test Coverage

## Context

The frontend currently has 9 Vitest unit tests across 3 files (`FleetSummary`, `ZoneCountsPanel`, `VehicleRow`).
All tests mock hooks at module level — they test component rendering in isolation but do not exercise the
HTTP layer, the full hook-to-component integration, or the rendered application in a real browser.

**Goal:** build a proper testing pyramid for a modern React application:
- **Unit** — fill remaining component and pure-function coverage gaps
- **Integration** — real TanStack Query + MSW intercepting fetch; no hook mocks
- **E2E** — Playwright, Chromium only, API mocked via `page.route()`

All tests must pass in CI (Node 22) and locally (Node 24). E2E must not require the FastAPI backend.

---

## Layer 1 — Unit tests (Vitest + Testing Library, hook mocks)

### New files

#### `frontend/src/test/apiFetch.test.ts`
Test the `apiFetch(path, params?)` function in `src/api/client.ts`:
- calls fetch with the correct base URL + path (`VITE_API_BASE_URL` from test env)
- appends multiple query params correctly
- returns parsed JSON on a 2xx response
- throws `Error("API error <status>: <path>")` on a non-ok response (test 404 and 500)

Use `vi.stubGlobal('fetch', vi.fn())` + `vi.unstubAllGlobals()` — do NOT use MSW here.

#### `frontend/src/test/VehicleList.test.tsx`
Mock `useVehicles` and `useVehicleAnomalies` (the latter is used internally by `VehicleRow`):
- loading state → paragraph contains "Loading vehicles"
- error state → element with class `error` containing "Failed to load vehicles"
- empty state (`data: []`) → "No vehicles reporting yet"
- populated (3 vehicles) → heading "Vehicles (3)", each vehicle ID in the DOM

### Additions to existing files

#### `frontend/src/test/VehicleRow.test.tsx` — 4 more tests
- battery bar fill is **red** (`background-color: rgb(239, 68, 68)`) when `battery_pct < 15`
- battery bar fill is **green** (`background-color: rgb(34, 197, 94)`) when `battery_pct >= 15`
- anomaly badge (`badge-orange`) is rendered when `useVehicleAnomalies` returns a non-empty array
- no anomaly badge when `useVehicleAnomalies` returns `[]`

Use `toHaveStyle` for color assertions (jest-dom normalises hex → rgb).

#### `frontend/src/test/ZoneCountsPanel.test.tsx` — 2 more tests
- loading state → "Loading zones"
- error state → element with class `error` containing "Failed to load zone counts"

---

## Layer 2 — Integration tests (Vitest + Testing Library + MSW, real QueryClient)

### Dependencies to add
```
npm install --save-dev msw
```

### MSW setup
- `frontend/src/test/mocks/handlers.ts` — default handlers for all 4 endpoints:
  - `GET /fleet/state` → `{ idle: 10, moving: 5, charging: 3, fault: 1, total: 19 }`
  - `GET /vehicles` → array of 2 vehicles (`v-01` moving 75%, `v-02` fault 8%)
  - `GET /zones/counts` → `{ aisle_a: 5, charging_bay_1: 12, pack_station: 3 }`
  - `GET /anomalies` → `[]`
- `frontend/src/test/mocks/server.ts` — `setupServer(...handlers)` from `msw/node`
- `frontend/src/test/setup.ts` — add MSW lifecycle:
  ```ts
  beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
  afterEach(() => server.resetHandlers())
  afterAll(() => server.close())
  ```

### New file: `frontend/src/test/integration/Dashboard.integration.test.tsx`
Render each component wrapped in a fresh `QueryClientProvider` (`retry: false`, `refetchInterval: false`).
Use `waitFor` to wait for async data to appear.

**FleetSummary:**
- shows loading state initially, then `19 vehicles` heading and `10` (idle) count

**VehicleList:**
- shows both vehicles after loading (`v-01`, `v-02`, heading `Vehicles (2)`)
- shows error state when server returns 500 (use `server.use(http.get(..., () => HttpResponse.error()))`)

**ZoneCountsPanel:**
- zones loaded and sorted: `charging bay 1` (12) first, `aisle a` (5) second, `pack station` (3) third
- shows error state when server returns 500

---

## Layer 3 — E2E (Playwright, Chromium, `page.route()`)

### Dependencies to add
```
npm install --save-dev @playwright/test
npx playwright install chromium --with-deps
```

### `frontend/playwright.config.ts`
- `testDir: './e2e'`
- `workers: 1` (avoids port conflicts)
- `reporter: [['html', { open: 'never' }]]`
- `baseURL: 'http://localhost:5173'`
- `webServer`: `npm run dev`, url `http://localhost:5173`, `reuseExistingServer: !process.env.CI`, timeout 30 s

### `frontend/e2e/fleet-dashboard.spec.ts`
`test.beforeEach` mocks all 4 API endpoints via `page.route()` (prevents real backend requirement):
- fleet/state: `{ idle: 10, moving: 5, charging: 3, fault: 2, total: 20 }`
- vehicles: `v-01` (moving, 75%) + `v-02` (fault, 8%)
- zones/counts: `{ aisle_a: 5, charging_bay_1: 20, pack_station: 2 }`
- `anomalies**`: `[]`

**7 scenarios:**
1. page title "Fleet Telemetry Monitor" is visible
2. "● LIVE" badge is visible
3. fleet summary shows "20 vehicles" and all 4 status labels
4. vehicle list shows "Vehicles (2)" heading and both IDs
5. fault vehicle row has `row-fault` CSS class
6. zone panel heading "Zone Counts" is visible and `zone-high` row exists
7. zones sorted descending: `charging bay 1` (20) → `aisle a` (5) → `pack station` (2)

---

## `package.json` scripts to add
```json
"test:e2e": "playwright test",
"test:e2e:ui": "playwright test --ui",
"test:e2e:report": "playwright show-report"
```

## `vite.config.ts` — add test env
```ts
test: {
  ...existing...
  env: {
    VITE_API_BASE_URL: 'http://localhost:8000',
  },
}
```

## CI — add E2E job to `.github/workflows/ci.yml`
New third job `e2e` (depends on nothing, runs in parallel):
- `actions/setup-node@v4` Node 22
- `npm ci`
- `npx playwright install chromium --with-deps`
- `npm run test:e2e`

---

## Done criteria
- [ ] `npm test` → **unit + integration**: all pass (target: ≥ 30 tests)
- [ ] `npm run test:e2e` → **7 E2E scenarios** pass on Chromium
- [ ] `npm run build` and `npx tsc --noEmit` still pass
- [ ] CI green (3 parallel jobs: backend, frontend, e2e)
- [ ] `docs/AI_INTERACTION_LOG.md` Interaction 24 logged
- [ ] CHANGELOG.md updated with new test entries
- [ ] Commit: `test(frontend): full test pyramid — unit, integration, E2E`

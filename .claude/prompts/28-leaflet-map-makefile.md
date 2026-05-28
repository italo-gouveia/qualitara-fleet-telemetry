# Prompt 28 — Live Vehicle Map (react-leaflet) + Makefile Improvements

## Goal

Add a geospatial live map panel to the React dashboard leveraging the `lat`/`lon` fields already present in every vehicle state. Vehicles should be visualised as coloured markers by status with an anomaly ring overlay. Expand the Makefile with developer shortcuts. Update the scalability roadmap to reflect BackgroundTasks as the realistic first step for WebSocket/SSE push before introducing Redis Pub/Sub.

## Implementation

### `frontend/src/components/VehicleMap.tsx` (new)

Full-width panel using `react-leaflet` + OpenStreetMap tiles (no API key needed):
- **Markers**: `CircleMarker` per vehicle; colour by status:
  - `moving` → `#22c55e` (green)
  - `charging` → `#3b82f6` (blue)
  - `idle` → `#64748b` (slate)
  - `fault` → `#ef4444` (red)
- **Anomaly ring**: dashed red `CircleMarker` (radius 14, non-interactive) for every vehicle that appears in the current anomalies window (`useAnomalies()` — existing hook, no extra fetch)
- **Tooltip**: vehicle ID + status on hover
- **Popup**: vehicle ID, status, battery %, coordinates, "⚠ Active anomaly" when applicable
- **Legend**: status colour dots + dashed ring indicator below the map
- **Data**: `useVehicles()` (existing hook, 2 s refetch) — TanStack Query deduplicates the request shared with VehicleList

### `frontend/src/App.tsx` (update)

Import `VehicleMap`; place `<VehicleMap />` between `<FleetSummary />` and the `<div className="panels">` grid.

### `frontend/src/App.css` (update)

Add: `.map-panel`, `.map-legend`, `.legend-item`, `.legend-dot`, `.legend-ring`, `.map-popup`, `.map-popup-id`, `.map-popup-coord`, `.map-popup-alert`.

### `frontend/package.json` (update)

Runtime deps: `leaflet`, `react-leaflet`
Dev deps: `@types/leaflet`

### `Makefile` (update)

Expand from 4 targets to 14 with inline `##` documentation for `make help`:

| Target | What it does |
|--------|-------------|
| `help` | Print all targets with descriptions |
| `test` | `pytest tests/ -v` |
| `test-frontend` | `npm test` (Vitest) |
| `test-e2e` | `npm run test:e2e` (Playwright) |
| `lint` | `ruff check` + `mypy` |
| `up` | `docker compose up --build` |
| `up-detached` | `docker compose up --build -d` |
| `down` | `docker compose down` |
| `reset` | `docker compose down -v && up --build` |
| `logs` | `docker compose logs -f` |
| `ps` | `docker compose ps` |
| `dev` | `fastapi dev app/main.py` (local, hot-reload) |
| `migrate` | `alembic upgrade head` |
| `simulate` | `python backend/scripts/simulate_fleet.py` |
| `load-test` | `docker compose --profile load-test up --build` |

### `README.md` (update)

- Stack table: Frontend row → add "Live vehicle map (react-leaflet/OSM)"; test count 39 → 46
- Scalability Roadmap: Dashboard delivery row → "**Step 1:** FastAPI `BackgroundTasks` + WebSocket/SSE (zero new infra) → **Step 2:** Redis Pub/Sub fan-out"
- Future Enhancements: remove delivered Leaflet row; replace with Leaflet enhancement ideas (zone polygons, trail history, clustering); update SSE/WebSocket entry to describe the BackgroundTasks-first path

## Tests

### Unit — `src/test/VehicleMap.test.tsx` (new, 7 tests)

Mock `react-leaflet` at module level and `leaflet/dist/leaflet.css` (jsdom has no canvas/SVG):
1. Loading state renders "Loading map…"
2. Error state renders `.error` element
3. Map container and at least 3 circle markers rendered for 3 vehicles
4. Count badge shows correct number
5. Popup content — vehicle ID and battery % present (`getAllByText` for duplicates)
6. Anomaly alert text visible when vehicle has active anomaly
7. All four status labels + "anomaly" present in legend

## Acceptance criteria

- [ ] `npm test` → **46 passed**
- [ ] `npx tsc -b --noEmit` → clean
- [ ] `npm run build` → clean
- [ ] `VehicleMap` panel visible in running stack at http://localhost:5173
- [ ] `make help` lists all 14 targets
- [ ] `make simulate` sends telemetry when stack is running

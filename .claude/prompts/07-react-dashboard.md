# Prompt 07 — React Dashboard

## Goal

Build the fleet monitoring dashboard. Three panels: vehicle list, zone counts, and anomaly overlay per vehicle.

## Agent

Read: `.claude/agents/senior-react-developer.agent.md`

## Tech

- React 18 + TypeScript (strict)
- Vite
- TanStack Query v5 for polling
- Fetch API (no axios needed for this scale)

## File Structure

```
frontend/src/
├── api/
│   ├── client.ts        # base fetch wrapper, BASE_URL from env
│   ├── vehicles.ts      # getVehicles(), getFleetState()
│   ├── anomalies.ts     # getAnomalies(vehicleId?)
│   └── zones.ts         # getZoneCounts()
├── types/
│   └── index.ts         # Vehicle, Anomaly, ZoneCount, FleetState
├── hooks/
│   ├── useFleetState.ts
│   ├── useVehicles.ts
│   ├── useZoneCounts.ts
│   └── useVehicleAnomalies.ts
├── components/
│   ├── VehicleList.tsx
│   ├── VehicleRow.tsx
│   ├── ZoneCountsPanel.tsx
│   └── FleetSummary.tsx
└── App.tsx
```

## Types (`types/index.ts`)

```typescript
export type VehicleStatus = "idle" | "moving" | "charging" | "fault";

export interface Vehicle {
  vehicle_id: string;
  status: VehicleStatus;
  battery_pct: number;
  lat: number;
  lon: number;
  updated_at: string;
}

export interface Anomaly {
  id: number;
  vehicle_id: string;
  detected_at: string;
  type: string;
  detail: Record<string, unknown>;
}

export interface ZoneCounts {
  [zone_id: string]: number;
}

export interface FleetState {
  idle: number;
  moving: number;
  charging: number;
  fault: number;
  total: number;
}
```

## Polling Setup

```typescript
// hooks/useVehicles.ts
export function useVehicles() {
  return useQuery({
    queryKey: ["vehicles"],
    queryFn: getVehicles,
    refetchInterval: 2000,
    staleTime: 1000,
  });
}
```

## VehicleRow Requirements

- Status badge with colors: idle=slate, moving=blue, charging=green, fault=red
- Battery bar (0–100%)
- Most recent anomaly type badge (if any) — fetch from `useVehicleAnomalies(vehicleId)`

## ZoneCounts Panel

- Sorted by count descending
- Show all 20 zones (even those with count 0)
- Highlight zones with count > 10 (arbitrarily — for visual interest)

## Environment

```
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
```

## Acceptance Criteria

- Dashboard loads without errors
- Vehicle list shows all vehicles present in DB
- Zone counts update after new ingest events
- Status badges show correct colors
- No TypeScript errors (`tsc --noEmit` passes)

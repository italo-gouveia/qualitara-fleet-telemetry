# Prompt 09 — Telemetry Simulator (Optional but Recommended)

## Goal

Create a small Python script that simulates 50 vehicles sending telemetry at 1 Hz. This makes the dashboard visually convincing during the review and doubles as a manual integration test.

## File

`backend/scripts/simulate_fleet.py`

## What It Does

- Spawns 50 asyncio tasks, one per vehicle (`v-01` through `v-50`)
- Each task sends one `POST /telemetry` per second
- Randomly varies `battery_pct`, `speed_mps`, `status`, and occasionally sets `zone_entered`
- Occasionally transitions a vehicle to `fault` (e.g. 1% chance per tick)
- Runs until Ctrl+C

## Script Skeleton

```python
import asyncio
import random
from datetime import datetime, timezone

import httpx

BASE_URL = "http://localhost:8000"
ZONES = [...]  # import from core.zones or duplicate

async def simulate_vehicle(vehicle_id: str, client: httpx.AsyncClient) -> None:
    current_status = "idle"
    battery = random.randint(60, 100)

    while True:
        battery = max(0, battery - random.randint(0, 2))
        speed = random.uniform(0, 3) if current_status == "moving" else 0.0

        # Occasionally enter a zone
        zone_entered = random.choice(ZONES) if random.random() < 0.05 else None

        # Occasionally fault
        if random.random() < 0.01:
            current_status = "fault"

        payload = {
            "vehicle_id": vehicle_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lat": 37.41 + random.uniform(-0.01, 0.01),
            "lon": -122.08 + random.uniform(-0.01, 0.01),
            "battery_pct": battery,
            "speed_mps": speed,
            "status": current_status,
            "error_codes": ["E001"] if current_status == "fault" else [],
            "zone_entered": zone_entered,
        }

        try:
            await client.post("/telemetry", json=payload, timeout=5)
        except Exception as e:
            print(f"[{vehicle_id}] Error: {e}")

        # Reset fault after one tick (so vehicle recovers)
        if current_status == "fault":
            current_status = "idle"

        await asyncio.sleep(1)

async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        tasks = [simulate_vehicle(f"v-{i:02d}", client) for i in range(1, 51)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
```

## Acceptance Criteria

- Script runs: `python backend/scripts/simulate_fleet.py`
- Dashboard shows vehicles populating within 5 seconds
- Zone counts increase over time
- Occasional anomalies appear in the vehicle list
- No uncaught exceptions after 30 seconds of runtime

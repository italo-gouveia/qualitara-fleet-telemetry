"""
Simulate 50 autonomous vehicles sending telemetry at 1 Hz.

Usage:
    python backend/scripts/simulate_fleet.py [--url http://localhost:8000]

Press Ctrl+C to stop.
"""
import argparse
import asyncio
import random
from datetime import UTC, datetime

import httpx

ZONES = [
    "inbound_dock_a", "inbound_dock_b", "receiving_staging",
    "aisle_a", "aisle_b", "aisle_c",
    "high_bay_1", "high_bay_2", "bulk_storage",
    "pick_zone_1", "pick_zone_2", "pack_station", "sort_belt",
    "outbound_dock_a", "outbound_dock_b", "shipping_staging",
    "charging_bay_1", "charging_bay_2", "charging_bay_3", "maintenance_bay",
]

STATUSES = ["idle", "moving", "charging"]


async def simulate_vehicle(vehicle_id: str, client: httpx.AsyncClient, base_url: str) -> None:
    status = random.choice(STATUSES)
    battery = random.randint(60, 100)
    lat = 37.41 + random.uniform(-0.05, 0.05)
    lon = -122.08 + random.uniform(-0.05, 0.05)

    while True:
        battery = max(0, battery - random.randint(0, 2))
        if battery == 0:
            battery = random.randint(60, 100)

        if random.random() < 0.01 and status != "fault":
            status = "fault"
        elif status == "fault":
            status = "idle"
        elif random.random() < 0.1:
            status = random.choice(STATUSES)

        lat += random.uniform(-0.001, 0.001)
        lon += random.uniform(-0.001, 0.001)
        speed = random.uniform(0.5, 3.0) if status == "moving" else 0.0
        zone_entered = random.choice(ZONES) if random.random() < 0.05 else None
        error_codes = ["E001"] if status == "fault" else []

        payload = {
            "vehicle_id": vehicle_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "battery_pct": battery,
            "speed_mps": round(speed, 2),
            "status": status,
            "error_codes": error_codes,
            "zone_entered": zone_entered,
        }

        try:
            r = await client.post(f"{base_url}/telemetry", json=payload, timeout=5.0)
            if r.status_code != 201:
                print(f"[{vehicle_id}] unexpected {r.status_code}: {r.text[:80]}")
        except Exception as exc:
            print(f"[{vehicle_id}] error: {exc}")

        await asyncio.sleep(1.0)


async def main(base_url: str) -> None:
    print(f"Simulating 50 vehicles → {base_url}  (Ctrl+C to stop)")
    async with httpx.AsyncClient() as client:
        tasks = [
            asyncio.create_task(simulate_vehicle(f"v-{i:02d}", client, base_url))
            for i in range(1, 51)
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            for t in tasks:
                t.cancel()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.url))
    except KeyboardInterrupt:
        print("\nSimulation stopped.")

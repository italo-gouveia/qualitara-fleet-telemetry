"""
Locust load test for Fleet Telemetry Monitor.

Serves two purposes:
  1. Load test — measures throughput, latency, and error rate under stress.
  2. Data population — generates realistic metric traffic so Grafana/Prometheus
     dashboards light up during a demo.

Usage (via Docker Compose):
  docker compose --profile load-test up --build
  Open http://localhost:8089 → set users / spawn rate → Start swarming.

Usage (standalone, backend running locally):
  pip install locust
  locust -f load-test/locustfile.py --host http://localhost:8000
"""

import random
from datetime import UTC, datetime

from locust import HttpUser, between, task

# All 50 vehicle IDs matching the simulator
VEHICLE_IDS = [f"v-{i:02d}" for i in range(1, 51)]

# Real zone names from app/core/zones.py
ZONES = [
    "inbound_dock_a",
    "inbound_dock_b",
    "receiving_staging",
    "aisle_a",
    "aisle_b",
    "aisle_c",
    "high_bay_1",
    "high_bay_2",
    "bulk_storage",
    "pick_zone_1",
    "pick_zone_2",
    "pack_station",
    "sort_belt",
    "outbound_dock_a",
    "outbound_dock_b",
    "shipping_staging",
    "charging_bay_1",
    "charging_bay_2",
    "charging_bay_3",
    "maintenance_bay",
]

# Exclude "fault" from load test — fault triggers mission cancellation side-effects
# that would contaminate the dataset with artificial maintenance records.
STATUSES = ["idle", "moving", "charging"]


def _random_zone() -> str | None:
    """Return a random zone 30 % of the time, None otherwise."""
    return random.choice(ZONES) if random.random() < 0.3 else None


def _telemetry_payload(vehicle_id: str) -> dict:
    return {
        "vehicle_id": vehicle_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "lat": round(random.uniform(51.50, 51.52), 6),
        "lon": round(random.uniform(-0.12, -0.08), 6),
        "battery_pct": random.randint(5, 100),
        "speed_mps": round(random.uniform(0.0, 4.5), 2),
        "status": random.choice(STATUSES),
        "error_codes": [],
        "zone_entered": _random_zone(),
    }


class FleetApiUser(HttpUser):
    """Simulates a mix of telemetry producers and dashboard consumers."""

    wait_time = between(0.05, 0.3)

    @task(10)
    def post_telemetry(self) -> None:
        """Core ingest path — highest weight, mirrors 1 Hz per vehicle load."""
        vehicle_id = random.choice(VEHICLE_IDS)
        self.client.post(
            "/telemetry",
            json=_telemetry_payload(vehicle_id),
            name="/telemetry",
        )

    @task(3)
    def get_fleet_state(self) -> None:
        """Dashboard header — polled frequently by the React frontend."""
        self.client.get("/fleet/state")

    @task(2)
    def get_vehicles(self) -> None:
        """Vehicle list view."""
        self.client.get("/vehicles")

    @task(2)
    def get_zone_counts(self) -> None:
        """Zone heatmap panel."""
        self.client.get("/zones/counts")

    @task(2)
    def get_anomalies(self) -> None:
        """Anomaly feed — queries last 100 events."""
        self.client.get("/anomalies")

    @task(2)
    def get_vehicle_by_id(self) -> None:
        """Row-click detail — random vehicle lookup."""
        vehicle_id = random.choice(VEHICLE_IDS)
        self.client.get(f"/vehicles/{vehicle_id}", name="/vehicles/[id]")

    @task(1)
    def get_health(self) -> None:
        """Healthcheck traffic — keeps the readiness probe metric populated."""
        self.client.get("/health")

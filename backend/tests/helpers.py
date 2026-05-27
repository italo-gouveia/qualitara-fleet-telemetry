from typing import Any


def make_event(**overrides: Any) -> dict[str, Any]:
    """Return a valid telemetry event payload dict, overridable per field."""
    base: dict[str, Any] = {
        "vehicle_id": "v-01",
        "timestamp": "2026-05-27T10:00:00Z",
        "lat": 37.41,
        "lon": -122.08,
        "battery_pct": 80,
        "speed_mps": 1.2,
        "status": "moving",
        "error_codes": [],
        "zone_entered": None,
    }
    return {**base, **overrides}

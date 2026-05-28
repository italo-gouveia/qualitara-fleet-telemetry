"""Unit tests for app/core/anomaly.py — pure-function rules, no I/O."""

from datetime import UTC, datetime

import pytest

from app.core.anomaly import (
    ANOMALY_RULES,
    AnomalyType,
    check_critical_battery,
    check_error_codes,
    check_fault_entered,
    check_low_battery,
    check_speed_anomaly,
)
from app.schemas.telemetry import TelemetryEventIn, VehicleStatus


def make_event(**overrides: object) -> TelemetryEventIn:
    """Return a valid TelemetryEventIn with safe defaults, overridable per field."""
    return TelemetryEventIn(
        vehicle_id="v-test",
        timestamp=datetime.now(UTC),
        lat=0.0,
        lon=0.0,
        battery_pct=overrides.pop("battery_pct", 80),  # type: ignore[arg-type]
        speed_mps=overrides.pop("speed_mps", 1.0),  # type: ignore[arg-type]
        status=overrides.pop("status", VehicleStatus.MOVING),  # type: ignore[arg-type]
        error_codes=overrides.pop("error_codes", []),  # type: ignore[arg-type]
        zone_entered=overrides.pop("zone_entered", None),  # type: ignore[arg-type]
        **overrides,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# check_low_battery
# ---------------------------------------------------------------------------


def test_low_battery_below_threshold_triggers_anomaly() -> None:
    assert check_low_battery(make_event(battery_pct=14)) == AnomalyType.LOW_BATTERY


def test_low_battery_at_threshold_returns_none() -> None:
    """Threshold is strictly <15, so 15 is NOT low battery."""
    assert check_low_battery(make_event(battery_pct=15)) is None


def test_low_battery_normal_level_returns_none() -> None:
    assert check_low_battery(make_event(battery_pct=80)) is None


# ---------------------------------------------------------------------------
# check_critical_battery
# ---------------------------------------------------------------------------


def test_critical_battery_below_threshold_triggers_anomaly() -> None:
    assert check_critical_battery(make_event(battery_pct=4)) == AnomalyType.CRITICAL_BATTERY


def test_critical_battery_at_threshold_returns_none() -> None:
    """Threshold is strictly <5, so 5 is NOT critical."""
    assert check_critical_battery(make_event(battery_pct=5)) is None


# ---------------------------------------------------------------------------
# check_fault_entered
# ---------------------------------------------------------------------------


def test_fault_entered_on_fault_status() -> None:
    assert check_fault_entered(make_event(status=VehicleStatus.FAULT)) == AnomalyType.FAULT_ENTERED


@pytest.mark.parametrize(
    "status", [VehicleStatus.IDLE, VehicleStatus.MOVING, VehicleStatus.CHARGING]
)
def test_fault_entered_non_fault_statuses_return_none(status: VehicleStatus) -> None:
    assert check_fault_entered(make_event(status=status)) is None


# ---------------------------------------------------------------------------
# check_speed_anomaly
# ---------------------------------------------------------------------------


def test_speed_anomaly_moving_vehicle_while_idle() -> None:
    assert (
        check_speed_anomaly(make_event(speed_mps=0.6, status=VehicleStatus.IDLE))
        == AnomalyType.SPEED_ANOMALY
    )


def test_speed_anomaly_at_threshold_returns_none() -> None:
    """Threshold is strictly >0.5, so 0.5 is NOT a speed anomaly."""
    assert check_speed_anomaly(make_event(speed_mps=0.5, status=VehicleStatus.IDLE)) is None


def test_speed_anomaly_fast_moving_vehicle_returns_none() -> None:
    """High speed is only anomalous when status is IDLE."""
    assert check_speed_anomaly(make_event(speed_mps=10.0, status=VehicleStatus.MOVING)) is None


# ---------------------------------------------------------------------------
# check_error_codes
# ---------------------------------------------------------------------------


def test_error_codes_present_triggers_anomaly() -> None:
    assert check_error_codes(make_event(error_codes=["E01"])) == AnomalyType.ERROR_CODE_REPORTED


def test_error_codes_empty_returns_none() -> None:
    assert check_error_codes(make_event(error_codes=[])) is None


def test_error_codes_multiple_codes_still_one_anomaly() -> None:
    result = check_error_codes(make_event(error_codes=["E01", "E02", "E99"]))
    assert result == AnomalyType.ERROR_CODE_REPORTED


# ---------------------------------------------------------------------------
# ANOMALY_RULES pipeline
# ---------------------------------------------------------------------------


def test_anomaly_rules_has_exactly_five_entries() -> None:
    """Guard against accidental removal or duplicate registration of rules."""
    assert len(ANOMALY_RULES) == 5


def test_anomaly_rules_all_rules_callable() -> None:
    event = make_event()
    for rule in ANOMALY_RULES:
        result = rule(event)
        assert result is None or isinstance(result, AnomalyType)


def test_anomaly_rules_multi_anomaly_event_detects_all() -> None:
    """An event with critically low battery, fault status, and error codes
    should trigger at least CRITICAL_BATTERY, LOW_BATTERY, FAULT_ENTERED,
    and ERROR_CODE_REPORTED."""
    event = make_event(battery_pct=4, status=VehicleStatus.FAULT, error_codes=["E01"])
    detected = [r(event) for r in ANOMALY_RULES if r(event) is not None]
    anomaly_types = set(detected)
    assert AnomalyType.CRITICAL_BATTERY in anomaly_types
    assert AnomalyType.LOW_BATTERY in anomaly_types
    assert AnomalyType.FAULT_ENTERED in anomaly_types
    assert AnomalyType.ERROR_CODE_REPORTED in anomaly_types
    assert len(detected) >= 4

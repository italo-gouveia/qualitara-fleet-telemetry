from collections.abc import Callable
from enum import StrEnum

from app.schemas.telemetry import TelemetryEventIn, VehicleStatus

LOW_BATTERY_THRESHOLD = 15
CRITICAL_BATTERY_THRESHOLD = 5
MAX_IDLE_SPEED_MPS = 0.5


class AnomalyType(StrEnum):
    LOW_BATTERY = "low_battery"
    CRITICAL_BATTERY = "critical_battery"
    FAULT_ENTERED = "fault_entered"
    SPEED_ANOMALY = "speed_anomaly"
    ERROR_CODE_REPORTED = "error_code_reported"


AnomalyRule = Callable[[TelemetryEventIn], AnomalyType | None]


def check_low_battery(event: TelemetryEventIn) -> AnomalyType | None:
    if event.battery_pct < LOW_BATTERY_THRESHOLD:
        return AnomalyType.LOW_BATTERY
    return None


def check_critical_battery(event: TelemetryEventIn) -> AnomalyType | None:
    if event.battery_pct < CRITICAL_BATTERY_THRESHOLD:
        return AnomalyType.CRITICAL_BATTERY
    return None


def check_fault_entered(event: TelemetryEventIn) -> AnomalyType | None:
    if event.status == VehicleStatus.FAULT:
        return AnomalyType.FAULT_ENTERED
    return None


def check_speed_anomaly(event: TelemetryEventIn) -> AnomalyType | None:
    if event.speed_mps > MAX_IDLE_SPEED_MPS and event.status == VehicleStatus.IDLE:
        return AnomalyType.SPEED_ANOMALY
    return None


def check_error_codes(event: TelemetryEventIn) -> AnomalyType | None:
    if event.error_codes:
        return AnomalyType.ERROR_CODE_REPORTED
    return None


# Each rule: (event) -> AnomalyType | None — add new rules here to extend detection.
ANOMALY_RULES: list[AnomalyRule] = [
    check_low_battery,
    check_critical_battery,
    check_fault_entered,
    check_speed_anomaly,
    check_error_codes,
]

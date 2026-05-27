from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.anomaly import AnomalyType
from app.database import dialect_insert
from app.models.anomaly import Anomaly
from app.models.telemetry import TelemetryEvent
from app.models.vehicle import VehicleState
from app.models.zone import ZoneCount
from app.schemas.telemetry import TelemetryEventIn


async def insert_telemetry_event(
    event: TelemetryEventIn, session: AsyncSession
) -> int:
    row = TelemetryEvent(
        vehicle_id=event.vehicle_id,
        timestamp=event.timestamp,
        lat=event.lat,
        lon=event.lon,
        battery_pct=event.battery_pct,
        speed_mps=event.speed_mps,
        status=event.status.value,
        error_codes=event.error_codes,
        zone_entered=event.zone_entered,
        ingested_at=datetime.now(UTC),
    )
    session.add(row)
    await session.flush()
    return row.id


async def upsert_vehicle_state(event: TelemetryEventIn, session: AsyncSession) -> None:
    now = datetime.now(UTC)
    stmt = (
        dialect_insert(VehicleState)
        .values(
            vehicle_id=event.vehicle_id,
            status=event.status.value,
            battery_pct=event.battery_pct,
            lat=event.lat,
            lon=event.lon,
            updated_at=now,
        )
        .on_conflict_do_update(
            index_elements=["vehicle_id"],
            set_={
                "status": event.status.value,
                "battery_pct": event.battery_pct,
                "lat": event.lat,
                "lon": event.lon,
                "updated_at": now,
            },
        )
    )
    await session.execute(stmt)


async def increment_zone_count(zone_id: str, session: AsyncSession) -> None:
    await session.execute(
        update(ZoneCount)
        .where(ZoneCount.zone_id == zone_id)
        .values(
            entry_count=ZoneCount.entry_count + 1,
            last_updated=datetime.now(UTC),
        )
    )


async def insert_anomaly(
    vehicle_id: str,
    anomaly_type: AnomalyType,
    detail: dict[str, object],
    telemetry_event_id: int,
    session: AsyncSession,
) -> None:
    session.add(
        Anomaly(
            vehicle_id=vehicle_id,
            detected_at=datetime.now(UTC),
            type=anomaly_type.value,
            detail=detail,
            telemetry_event_id=telemetry_event_id,
        )
    )

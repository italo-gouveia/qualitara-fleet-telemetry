from sqlalchemy.ext.asyncio import AsyncSession

from app.core.anomaly import ANOMALY_RULES
from app.repositories.telemetry_repository import (
    increment_zone_count,
    insert_anomaly,
    insert_telemetry_event,
    upsert_vehicle_state,
)
from app.schemas.telemetry import IngestResult, TelemetryEventIn


async def ingest_event(event: TelemetryEventIn, session: AsyncSession) -> IngestResult:
    """Write one telemetry event and all derived side-effects in the caller's transaction."""
    event_id = await insert_telemetry_event(event, session)
    await upsert_vehicle_state(event, session)

    if event.zone_entered:
        await increment_zone_count(event.zone_entered, session)

    anomaly_types = [rule(event) for rule in ANOMALY_RULES]
    detected = [t for t in anomaly_types if t is not None]
    for anomaly_type in detected:
        await insert_anomaly(
            vehicle_id=event.vehicle_id,
            anomaly_type=anomaly_type,
            detail={"battery_pct": event.battery_pct, "status": event.status},
            telemetry_event_id=event_id,
            session=session,
        )

    return IngestResult(id=event_id, anomalies_detected=len(detected))

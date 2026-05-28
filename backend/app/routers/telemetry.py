from fastapi import APIRouter, status

from app.database import SessionDep
from app.schemas.telemetry import IngestResult, TelemetryEventIn
from app.services.telemetry import ingest_event

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("", response_model=IngestResult, status_code=status.HTTP_201_CREATED)
async def post_telemetry(event: TelemetryEventIn, session: SessionDep) -> IngestResult:
    result = await ingest_event(event, session)
    await session.commit()
    return result

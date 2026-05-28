import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.config import settings
from app.core.exception_handlers import unhandled_exception_handler
from app.core.logging_config import setup_logging
from app.core.zones import ZONES
from app.database import AsyncSessionLocal, SessionDep, engine
from app.middleware.request_logging import RequestLoggingMiddleware
from app.routers.anomaly import router as anomaly_router
from app.routers.fleet import router as fleet_router
from app.routers.telemetry import router as telemetry_router
from app.routers.vehicle import router as vehicle_router

setup_logging(settings.log_level, settings.log_format)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    db_host = settings.database_url.split("@")[-1]
    logger.info("Starting Fleet Telemetry Monitor", extra={"db": db_host})
    await _seed_zone_counts()
    yield
    await engine.dispose()
    logger.info("Fleet Telemetry Monitor stopped")


async def _seed_zone_counts() -> None:
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text(
                "INSERT INTO zone_counts (zone_id, entry_count) "
                "VALUES (:zone_id, 0) ON CONFLICT (zone_id) DO NOTHING"
            ),
            [{"zone_id": z} for z in ZONES],
        )


app = FastAPI(
    title="Fleet Telemetry Monitor",
    description=(
        "Real-time monitoring API for 50 autonomous industrial vehicles.\n\n"
        "Ingest telemetry at 1 Hz, track vehicle states, zone entry counts, "
        "and anomaly events. See `docs/ADR.md` for architecture decisions."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(telemetry_router)
app.include_router(fleet_router)
app.include_router(vehicle_router)
app.include_router(anomaly_router)

Instrumentator().instrument(app).expose(app)


@app.get("/health", tags=["ops"])
async def health(session: SessionDep, response: Response) -> dict[str, str]:
    """Liveness + readiness probe: returns 503 if the database is unreachable."""
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        logger.warning("health_check_db_unavailable")
        response.status_code = 503
        return {"status": "unavailable"}

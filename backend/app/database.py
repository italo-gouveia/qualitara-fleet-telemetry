from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


def dialect_insert(model: type) -> Any:
    """Return dialect-aware Insert for upsert operations (PostgreSQL or SQLite)."""
    if engine.dialect.name == "postgresql":
        return pg_insert(model)
    return sqlite_insert(model)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# Reusable Annotated dependency — use as `session: SessionDep` in all handlers
SessionDep = Annotated[AsyncSession, Depends(get_session)]

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ZoneCount(Base):
    __tablename__ = "zone_counts"

    zone_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    entry_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

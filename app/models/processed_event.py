"""Модель обробленої події платформи (для ідемпотентності)."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProcessedEvent(Base):
    """Подія платформи, яку вже було оброблено."""

    __tablename__ = "processed_events"
    __table_args__ = (
        UniqueConstraint("platform", "platform_event_id", name="uq_processed_events_platform_event"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(20))
    platform_event_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

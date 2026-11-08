"""Модель користувача бота."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app._detail.constants import DISPLAY_NAME_MAX_LENGTH
from app.models.base import Base


class BotUser(Base):
    """Користувач, ідентифікований незмінним platform_user_id."""

    __tablename__ = "bot_users"
    __table_args__ = (UniqueConstraint("platform_user_id", name="uq_bot_users_platform_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_user_id: Mapped[int] = mapped_column(BigInteger)
    display_name: Mapped[str | None] = mapped_column(String(DISPLAY_NAME_MAX_LENGTH))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

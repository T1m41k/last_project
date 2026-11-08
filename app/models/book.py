"""Модель книги (основна предметна сутність)."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app._detail.constants import (
    BOOK_AUTHOR_MAX_LENGTH,
    BOOK_NOTE_MAX_LENGTH,
    BOOK_TITLE_MAX_LENGTH,
)
from app.models.base import Base


class Book(Base):
    """Запис про книгу, що належить одному користувачу."""

    __tablename__ = "books"
    __table_args__ = (Index("ix_books_owner_id_id", "owner_id", "id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("bot_users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(BOOK_TITLE_MAX_LENGTH))
    author: Mapped[str] = mapped_column(String(BOOK_AUTHOR_MAX_LENGTH))
    pages: Mapped[int]
    status: Mapped[str] = mapped_column(String(20))
    note: Mapped[str | None] = mapped_column(String(BOOK_NOTE_MAX_LENGTH))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

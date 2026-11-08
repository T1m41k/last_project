"""Схеми адміністративного API."""

from pydantic import BaseModel, Field


class AdminStatsResponse(BaseModel):
    """Статистика бота."""

    users_count: int = Field(ge=0, description="Кількість зареєстрованих користувачів")
    books_count: int = Field(ge=0, description="Кількість записів про книги")

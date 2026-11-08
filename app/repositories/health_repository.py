"""Репозиторій перевірки готовності бази даних."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class HealthRepository:
    """Найпростіший запит до бази даних."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ping(self) -> None:
        """Виконати SELECT 1; кидає виняток, якщо БД недоступна."""
        await self._session.execute(text("SELECT 1"))

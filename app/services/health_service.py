"""Сервіс перевірки готовності."""

from sqlalchemy.exc import SQLAlchemyError

from app.repositories.health_repository import HealthRepository


class HealthService:
    """Перевірка доступності бази даних."""

    def __init__(self, health: HealthRepository) -> None:
        self._health = health

    async def is_database_ready(self) -> bool:
        """Перевірити, чи відповідає база даних.

        Returns
        -------
        bool
            True, якщо запит виконано успішно.
        """
        try:
            await self._health.ping()
        except (SQLAlchemyError, OSError):
            return False
        return True

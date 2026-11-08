"""Сервіс статистики для адміністраторів."""

from dataclasses import dataclass

from app.repositories.book_repository import BookRepository
from app.repositories.user_repository import UserRepository


@dataclass(frozen=True)
class StatsSnapshot:
    """Знімок статистики."""

    users_count: int
    books_count: int


class StatsService:
    """Підрахунок користувачів і записів."""

    def __init__(self, users: UserRepository, books: BookRepository) -> None:
        self._users = users
        self._books = books

    async def collect(self) -> StatsSnapshot:
        """Зібрати статистику.

        Returns
        -------
        StatsSnapshot
            Кількість користувачів і записів.
        """
        return StatsSnapshot(
            users_count=await self._users.count(), books_count=await self._books.count_all()
        )

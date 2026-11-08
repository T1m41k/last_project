"""Складання сервісів для однієї сесії бази даних."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.book_repository import BookRepository
from app.repositories.dialog_repository import DialogRepository
from app.repositories.event_repository import EventRepository
from app.repositories.health_repository import HealthRepository
from app.repositories.user_repository import UserRepository
from app.services.add_book_dialog_service import AddBookDialogService
from app.services.book_service import BookService
from app.services.dialog_service import DialogService
from app.services.event_service import EventService
from app.services.health_service import HealthService
from app.services.stats_service import StatsService
from app.services.user_service import UserService


@dataclass(frozen=True)
class Services:
    """Набір сервісів, спільний для бота та FastAPI."""

    users: UserService
    books: BookService
    dialogs: DialogService
    add_book: AddBookDialogService
    events: EventService
    stats: StatsService
    health: HealthService


def build_services(session: AsyncSession) -> Services:
    """Створити сервіси поверх однієї сесії.

    Parameters
    ----------
    session : AsyncSession
        Відкрита сесія бази даних.

    Returns
    -------
    Services
        Набір сервісів.
    """
    user_repository = UserRepository(session)
    book_repository = BookRepository(session)
    books = BookService(book_repository)
    dialogs = DialogService(DialogRepository(session))
    return Services(
        users=UserService(user_repository),
        books=books,
        dialogs=dialogs,
        add_book=AddBookDialogService(dialogs, books),
        events=EventService(EventRepository(session)),
        stats=StatsService(user_repository, book_repository),
        health=HealthService(HealthRepository(session)),
    )

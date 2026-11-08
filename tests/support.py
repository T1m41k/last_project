"""Допоміжні об'єкти тестів: підроблені відправник, репозиторії та чат."""

import itertools
from typing import Any

from app.bot.contracts import IncomingMessage
from app.bot.handlers import BotHandlers
from app.models import Book, DialogState

_EVENT_COUNTER = itertools.count(1)


def next_event_id() -> int:
    """Повернути унікальний id події для тесту."""
    return next(_EVENT_COUNTER)


class FakeSender:
    """Підроблений відправник: запам'ятовує повідомлення або кидає помилку."""

    def __init__(self) -> None:
        self.sent: list[tuple[int, str]] = []
        self.error: Exception | None = None

    async def send_text(self, chat_id: int, text: str) -> None:
        """Записати повідомлення або викликати налаштовану помилку."""
        if self.error is not None:
            raise self.error
        self.sent.append((chat_id, text))

    def last_text(self, chat_id: int) -> str:
        """Повернути останню відповідь у чат."""
        return [text for target, text in self.sent if target == chat_id][-1]


class Chat:
    """Імітація приватного чату користувача з ботом."""

    def __init__(self, handlers: BotHandlers, sender: FakeSender, user_id: int) -> None:
        self._handlers = handlers
        self._sender = sender
        self.user_id = user_id

    async def say(self, text: str) -> str:
        """Надіслати повідомлення боту й повернути його відповідь."""
        await self._handlers.handle_message(
            IncomingMessage(
                event_id=next_event_id(),
                platform_user_id=self.user_id,
                text=text,
                display_name="Тест Користувач",
            )
        )
        return self._sender.last_text(self.user_id)


class FakeBookRepository:
    """Репозиторій книг у пам'яті з тим самим інтерфейсом."""

    def __init__(self) -> None:
        self.items: dict[int, Book] = {}
        self._next_id = 1

    async def add(self, **fields: Any) -> Book:
        """Створити книгу."""
        book = Book(id=self._next_id, **fields)
        self.items[book.id] = book
        self._next_id += 1
        return book

    async def get_owned(self, owner_id: int, book_id: int) -> Book | None:
        """Знайти книгу власника."""
        book = self.items.get(book_id)
        return book if book is not None and book.owner_id == owner_id else None

    async def list_owned(self, owner_id: int, *, limit: int, offset: int) -> list[Book]:
        """Повернути сторінку книг власника за спаданням id."""
        owned = sorted((b for b in self.items.values() if b.owner_id == owner_id), key=lambda b: -b.id)
        return owned[offset : offset + limit]

    async def count_owned(self, owner_id: int) -> int:
        """Порахувати книги власника."""
        return sum(1 for book in self.items.values() if book.owner_id == owner_id)

    async def update(self, book: Book, values: dict[str, Any]) -> Book:
        """Оновити поля."""
        for name, value in values.items():
            setattr(book, name, value)
        return book

    async def delete(self, book: Book) -> None:
        """Видалити книгу."""
        del self.items[book.id]


class FakeDialogRepository:
    """Репозиторій діалогів у пам'яті."""

    def __init__(self) -> None:
        self.states: dict[int, DialogState] = {}

    async def get(self, user_id: int) -> DialogState | None:
        """Отримати стан."""
        return self.states.get(user_id)

    async def save(self, user_id: int, flow: str, step: str, data: dict[str, Any]) -> DialogState:
        """Зберегти стан."""
        state = DialogState(user_id=user_id, flow=flow, step=step, data=data)
        self.states[user_id] = state
        return state

    async def delete_for_user(self, user_id: int) -> bool:
        """Видалити стан."""
        return self.states.pop(user_id, None) is not None

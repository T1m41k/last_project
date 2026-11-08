"""Модульні тести сервісів на репозиторіях у пам'яті."""

import pytest

from app.core.exceptions import BookNotFoundError, ValidationFailedError
from app.services.add_book_dialog_service import AddBookDialogService
from app.services.book_service import BookService
from app.services.dialog_service import DialogService
from tests.support import FakeBookRepository, FakeDialogRepository


async def test_create_validates_and_normalizes() -> None:
    """Створення нормалізує текст і ставить статус за замовчуванням."""
    service = BookService(FakeBookRepository())
    book = await service.create(1, title="  Дюна ", author="Герберт", pages=600)
    assert (book.title, book.status, book.note) == ("Дюна", "planned", None)
    with pytest.raises(ValidationFailedError):
        await service.create(1, title="", author="А", pages=10)
    with pytest.raises(ValidationFailedError):
        await service.create(1, title="Т", author="А", pages=0)


async def test_get_hides_foreign_books() -> None:
    """Чужа книга поводиться як відсутня."""
    service = BookService(FakeBookRepository())
    book = await service.create(1, title="Т", author="А", pages=10)
    with pytest.raises(BookNotFoundError):
        await service.get(2, book.id)
    with pytest.raises(BookNotFoundError):
        await service.delete(2, book.id)


async def test_update_field_and_delete() -> None:
    """Оновлення поля і видалення власної книги."""
    service = BookService(FakeBookRepository())
    book = await service.create(1, title="Т", author="А", pages=10)
    updated = await service.update_field(1, book.id, "статус", "finished")
    assert updated.status == "finished"
    assert (await service.update_field(1, book.id, "pages", "55")).pages == 55
    assert (await service.update_field(1, book.id, "note", "ок")).note == "ок"
    assert (await service.update_field(1, book.id, "note", "-")).note is None
    assert (await service.update_field(1, book.id, "title", "Нова")).title == "Нова"
    assert (await service.update_field(1, book.id, "author", "Інший")).author == "Інший"
    with pytest.raises(ValidationFailedError):
        await service.update_field(1, book.id, "pages", "abc")
    with pytest.raises(ValidationFailedError):
        await service.update_field(1, book.id, "колір", "синій")
    await service.delete(1, book.id)
    with pytest.raises(BookNotFoundError):
        await service.get(1, book.id)


async def test_list_page_is_stable_and_paged() -> None:
    """Список повертає книги за спаданням id зі зсувом."""
    service = BookService(FakeBookRepository())
    for index in range(5):
        await service.create(1, title=f"Т{index}", author="А", pages=10)
    books, total = await service.list_page(1, limit=2, offset=2)
    assert total == 5
    assert [book.id for book in books] == [3, 2]


def build_dialog() -> tuple[AddBookDialogService, FakeBookRepository, FakeDialogRepository]:
    """Зібрати діалог на репозиторіях у пам'яті."""
    books, states = FakeBookRepository(), FakeDialogRepository()
    return AddBookDialogService(DialogService(states), BookService(books)), books, states


async def test_dialog_happy_path_creates_book() -> None:
    """Повний діалог зберігає книгу й очищає стан."""
    dialog, books, states = build_dialog()
    await dialog.start(1)
    for answer in ("Дюна", "Герберт", "600"):
        outcome = await dialog.answer(1, states.states[1], answer)
        assert outcome.error is None
    assert states.states[1].step == "confirm"
    outcome = await dialog.answer(1, states.states[1], "так")
    assert outcome.book is not None and len(books.items) == 1
    assert 1 not in states.states


async def test_dialog_invalid_input_keeps_step() -> None:
    """Помилка валідації не змінює крок."""
    dialog, _, states = build_dialog()
    await dialog.start(1)
    outcome = await dialog.answer(1, states.states[1], "а" * 500)
    assert outcome.error is not None and outcome.step == "title"
    assert states.states[1].step == "title"


async def test_dialog_decline_and_unclear_answer() -> None:
    """Відмова скасовує діалог, незрозуміла відповідь повторює запит."""
    dialog, books, states = build_dialog()
    await dialog.start(1)
    for answer in ("Дюна", "Герберт", "600"):
        await dialog.answer(1, states.states[1], answer)
    assert (await dialog.answer(1, states.states[1], "можливо")).error is not None
    assert (await dialog.answer(1, states.states[1], "ні")).cancelled
    assert not books.items and 1 not in states.states


async def test_dialog_unknown_step_is_reported() -> None:
    """Пошкоджений крок дає зрозумілу помилку."""
    dialog, _, states = build_dialog()
    state = await DialogService(states).start(1, "add_book", "невідомий")
    assert (await dialog.answer(1, state, "щось")).error is not None

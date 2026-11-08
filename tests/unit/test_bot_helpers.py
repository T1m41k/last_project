"""Модульні тести допоміжних функцій бота та форматування."""

import pytest

from app._detail.bot.helpers import is_no, is_yes, parse_command, truncate_message
from app._detail.constants import MAX_MESSAGE_LENGTH
from app._detail.formatting.helpers import (
    format_book_details,
    format_book_line,
    format_book_list,
    format_summary,
)
from app.models import Book


def make_book(book_id: int = 1, note: str | None = None) -> Book:
    """Створити книгу без звернення до БД."""
    return Book(id=book_id, owner_id=1, title="Дюна", author="Ф. Герберт", pages=600, status="reading", note=note)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("/start", ("start", "")),
        ("/Book@my_bot 5", ("book", "5")),
        ("  /update 1 title Нова назва ", ("update", "1 title Нова назва")),
        ("/", ("", "")),
        ("привіт", None),
        ("", None),
    ],
)
def test_parse_command(text: str, expected: tuple[str, str] | None) -> None:
    """Команди розбираються на назву й аргументи."""
    assert parse_command(text) == expected


def test_yes_no_answers() -> None:
    """Розпізнавання ствердних і заперечних відповідей."""
    assert is_yes(" Так ") and is_yes("y")
    assert is_no("НІ") and is_no("no")
    assert not is_yes("можливо") and not is_no("можливо")


def test_truncate_message() -> None:
    """Довгі повідомлення обрізаються до ліміту."""
    assert truncate_message("коротко") == "коротко"
    assert len(truncate_message("а" * (MAX_MESSAGE_LENGTH + 50))) == MAX_MESSAGE_LENGTH


def test_format_book_line_and_details() -> None:
    """Форматування рядка та деталей книги."""
    book = make_book(note="класика")
    assert format_book_line(book) == "#1 · Дюна — Ф. Герберт (600 с.) · читаю"
    details = format_book_details(book)
    assert "Нотатка: класика" in details
    assert "Нотатка: —" in format_book_details(make_book())


def test_format_book_list_shows_next_page_hint() -> None:
    """Підказка про наступну сторінку з'являється, коли є ще записи."""
    assert "/list 2" in format_book_list([make_book()], page=1, total=25)
    assert "/list" not in format_book_list([make_book()], page=1, total=1).splitlines()[-1]


def test_format_summary() -> None:
    """Підсумок діалогу містить усі поля."""
    summary = format_summary({"title": "А", "author": "Б", "pages": 3})
    assert "Назва: А" in summary and "Автор: Б" in summary and "Сторінок: 3" in summary

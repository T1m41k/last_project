"""Допоміжні функції форматування відповідей бота."""

from collections.abc import Mapping, Sequence
from typing import Any

from app._detail.constants import LIST_PAGE_SIZE, STATUS_LABELS
from app.models import Book


def format_book_line(book: Book) -> str:
    """Сформувати короткий рядок про книгу для списку.

    Parameters
    ----------
    book : Book
        Книга.

    Returns
    -------
    str
        Рядок виду «#1 · Назва — Автор (320 с.) · читаю».
    """
    label = STATUS_LABELS.get(book.status, book.status)
    return f"#{book.id} · {book.title} — {book.author} ({book.pages} с.) · {label}"


def format_book_details(book: Book) -> str:
    """Сформувати докладний опис книги.

    Parameters
    ----------
    book : Book
        Книга.

    Returns
    -------
    str
        Багаторядковий опис.
    """
    label = STATUS_LABELS.get(book.status, book.status)
    return "\n".join(
        [
            f"Книга #{book.id}",
            f"Назва: {book.title}",
            f"Автор: {book.author}",
            f"Сторінок: {book.pages}",
            f"Статус: {label}",
            f"Нотатка: {book.note or '—'}",
        ]
    )


def format_book_list(books: Sequence[Book], page: int, total: int) -> str:
    """Сформувати сторінку списку книг.

    Parameters
    ----------
    books : Sequence[Book]
        Книги поточної сторінки.
    page : int
        Номер сторінки (з 1).
    total : int
        Загальна кількість книг користувача.

    Returns
    -------
    str
        Текст зі списком і підказкою щодо наступної сторінки.
    """
    lines = [f"Ваші книги (сторінка {page}, усього {total}):"]
    lines.extend(format_book_line(book) for book in books)
    if page * LIST_PAGE_SIZE < total:
        lines.append(f"Наступна сторінка: /list {page + 1}")
    return "\n".join(lines)


def format_summary(data: Mapping[str, Any]) -> str:
    """Сформувати підсумок даних діалогу перед підтвердженням.

    Parameters
    ----------
    data : Mapping[str, Any]
        Зібрані дані (title, author, pages).

    Returns
    -------
    str
        Багаторядковий підсумок.
    """
    return "\n".join(
        [
            f"Назва: {data.get('title', '—')}",
            f"Автор: {data.get('author', '—')}",
            f"Сторінок: {data.get('pages', '—')}",
        ]
    )

"""Бізнес-правила для записів про книги."""

from app._detail.constants import (
    BOOK_AUTHOR_MAX_LENGTH,
    BOOK_TITLE_MAX_LENGTH,
    DEFAULT_STATUS,
    FIELD_AUTHOR,
    FIELD_NOTE,
    FIELD_PAGES,
    FIELD_STATUS,
    FIELD_TITLE,
)
from app._detail.validation.helpers import (
    ensure_pages_in_range,
    normalize_text,
    parse_field_name,
    parse_note,
    parse_pages,
    parse_status,
)
from app.core.exceptions import BookNotFoundError
from app.models import Book
from app.repositories.book_repository import BookRepository


class BookService:
    """CRUD книг із перевіркою введених значень і прав власника."""

    def __init__(self, books: BookRepository) -> None:
        self._books = books

    async def create(
        self,
        owner_id: int,
        *,
        title: str,
        author: str,
        pages: int,
        status: str = DEFAULT_STATUS,
        note: str | None = None,
    ) -> Book:
        """Створити книгу після валідації.

        Parameters
        ----------
        owner_id : int
            Внутрішній id власника.
        title : str
            Назва.
        author : str
            Автор.
        pages : int
            Кількість сторінок.
        status : str
            Код або назва статусу.
        note : str | None
            Нотатка.

        Returns
        -------
        Book
            Створена книга.

        Raises
        ------
        ValidationFailedError
            Якщо якесь значення некоректне.
        """
        return await self._books.add(
            owner_id=owner_id,
            title=normalize_text(title, field_label="назва", max_length=BOOK_TITLE_MAX_LENGTH),
            author=normalize_text(author, field_label="автор", max_length=BOOK_AUTHOR_MAX_LENGTH),
            pages=ensure_pages_in_range(pages),
            status=parse_status(status),
            note=None if note is None else parse_note(note),
        )

    async def list_page(
        self, owner_id: int, *, limit: int, offset: int
    ) -> tuple[list[Book], int]:
        """Отримати сторінку книг користувача та їх загальну кількість.

        Parameters
        ----------
        owner_id : int
            Внутрішній id власника.
        limit : int
            Розмір сторінки.
        offset : int
            Зсув.

        Returns
        -------
        tuple[list[Book], int]
            Книги сторінки та загальна кількість.
        """
        books = await self._books.list_owned(owner_id, limit=limit, offset=offset)
        return list(books), await self._books.count_owned(owner_id)

    async def get(self, owner_id: int, book_id: int) -> Book:
        """Отримати власну книгу.

        Parameters
        ----------
        owner_id : int
            Внутрішній id власника.
        book_id : int
            Id книги.

        Returns
        -------
        Book
            Книга.

        Raises
        ------
        BookNotFoundError
            Якщо книги немає або вона належить іншому користувачу.
        """
        book = await self._books.get_owned(owner_id, book_id)
        if book is None:
            raise BookNotFoundError(f"Запис #{book_id} не знайдено.")
        return book

    async def update_field(self, owner_id: int, book_id: int, field: str, raw_value: str) -> Book:
        """Оновити одне поле власної книги.

        Parameters
        ----------
        owner_id : int
            Внутрішній id власника.
        book_id : int
            Id книги.
        field : str
            Назва поля (title, author, pages, status, note або українська).
        raw_value : str
            Нове значення у текстовому вигляді.

        Returns
        -------
        Book
            Оновлена книга.

        Raises
        ------
        BookNotFoundError
            Якщо книги немає або вона чужа.
        ValidationFailedError
            Якщо поле чи значення некоректні.
        """
        book = await self.get(owner_id, book_id)
        name = parse_field_name(field)
        return await self._books.update(book, {name: self._parse_value(name, raw_value)})

    async def delete(self, owner_id: int, book_id: int) -> None:
        """Видалити власну книгу.

        Parameters
        ----------
        owner_id : int
            Внутрішній id власника.
        book_id : int
            Id книги.

        Raises
        ------
        BookNotFoundError
            Якщо книги немає або вона чужа.
        """
        await self._books.delete(await self.get(owner_id, book_id))

    @staticmethod
    def _parse_value(name: str, raw_value: str) -> str | int | None:
        """Розібрати значення відповідно до типу поля."""
        if name == FIELD_PAGES:
            return parse_pages(raw_value)
        if name == FIELD_STATUS:
            return parse_status(raw_value)
        if name == FIELD_NOTE:
            return parse_note(raw_value)
        if name == FIELD_TITLE:
            return normalize_text(raw_value, field_label="назва", max_length=BOOK_TITLE_MAX_LENGTH)
        if name == FIELD_AUTHOR:
            return normalize_text(raw_value, field_label="автор", max_length=BOOK_AUTHOR_MAX_LENGTH)
        raise AssertionError(name)

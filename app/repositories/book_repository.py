"""Репозиторій книг."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Book


class BookRepository:
    """Запити до таблиці books; усі вибірки обмежені власником."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        *,
        owner_id: int,
        title: str,
        author: str,
        pages: int,
        status: str,
        note: str | None,
    ) -> Book:
        """Створити книгу.

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
            Код статусу.
        note : str | None
            Нотатка.

        Returns
        -------
        Book
            Збережена книга з заповненими серверними полями.
        """
        book = Book(
            owner_id=owner_id, title=title, author=author, pages=pages, status=status, note=note
        )
        self._session.add(book)
        await self._session.flush()
        await self._session.refresh(book)
        return book

    async def get_owned(self, owner_id: int, book_id: int) -> Book | None:
        """Знайти книгу власника.

        Parameters
        ----------
        owner_id : int
            Внутрішній id власника.
        book_id : int
            Id книги.

        Returns
        -------
        Book | None
            Книга або None, якщо її немає чи вона чужа.
        """
        result = await self._session.execute(
            select(Book).where(Book.id == book_id, Book.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def list_owned(self, owner_id: int, *, limit: int, offset: int) -> Sequence[Book]:
        """Отримати сторінку книг власника зі стабільним сортуванням.

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
        Sequence[Book]
            Книги, відсортовані за id за спаданням.
        """
        result = await self._session.execute(
            select(Book)
            .where(Book.owner_id == owner_id)
            .order_by(Book.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def count_owned(self, owner_id: int) -> int:
        """Порахувати книги власника.

        Parameters
        ----------
        owner_id : int
            Внутрішній id власника.

        Returns
        -------
        int
            Кількість книг.
        """
        result = await self._session.execute(
            select(func.count()).select_from(Book).where(Book.owner_id == owner_id)
        )
        return result.scalar_one()

    async def count_all(self) -> int:
        """Порахувати всі книги.

        Returns
        -------
        int
            Загальна кількість книг.
        """
        result = await self._session.execute(select(func.count()).select_from(Book))
        return result.scalar_one()

    async def update(self, book: Book, values: dict[str, str | int | None]) -> Book:
        """Оновити поля книги.

        Parameters
        ----------
        book : Book
            Книга, отримана з цієї сесії.
        values : dict[str, str | int | None]
            Нові значення полів.

        Returns
        -------
        Book
            Оновлена книга.
        """
        for name, value in values.items():
            setattr(book, name, value)
        await self._session.flush()
        await self._session.refresh(book)
        return book

    async def delete(self, book: Book) -> None:
        """Видалити книгу.

        Parameters
        ----------
        book : Book
            Книга, отримана з цієї сесії.
        """
        await self._session.delete(book)
        await self._session.flush()

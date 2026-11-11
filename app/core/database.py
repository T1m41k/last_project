"""Підключення до PostgreSQL (Neon) через асинхронний SQLAlchemy."""

from sqlalchemy import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app._detail.constants import ASYNC_DRIVER


def to_async_url(url: str) -> str:
    """Перетворити стандартний URL Neon на URL для драйвера asyncpg.

    Параметр ``sslmode`` замінюється на ``ssl`` (TLS зберігається),
    ``channel_binding`` відкидається, бо asyncpg його не розуміє.

    Parameters
    ----------
    url : str
        URL виду ``postgresql://user:pass@host/db?sslmode=require``.

    Returns
    -------
    str
        URL із драйвером ``postgresql+asyncpg``.
    """
    parsed = make_url(url)
    query: dict[str, str | tuple[str, ...]] = dict(parsed.query)
    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)
    if sslmode is not None and "ssl" not in query:
        query["ssl"] = sslmode
    return parsed.set(drivername=ASYNC_DRIVER, query=query).render_as_string(hide_password=False)


def create_engine(url: str) -> AsyncEngine:
    """Створити асинхронний рушій із перевіркою з'єднань.

    Parameters
    ----------
    url : str
        URL бази даних у стандартному форматі.

    Returns
    -------
    AsyncEngine
        Рушій SQLAlchemy.
    """
    return create_async_engine(to_async_url(url), pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Створити фабрику сесій.

    Parameters
    ----------
    engine : AsyncEngine
        Рушій, до якого прив'язуються сесії.

    Returns
    -------
    async_sessionmaker[AsyncSession]
        Фабрика сесій без автоматичного закінчення терміну дії об'єктів.
    """
    return async_sessionmaker(engine, expire_on_commit=False)

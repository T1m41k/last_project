"""Спільні фікстури тестів."""

import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.bot.handlers import BotHandlers
from app.core.config import Settings
from app.core.database import create_session_factory, to_async_url
from app.main import create_app
from tests.support import Chat, FakeSender

ADMIN_KEY = "test-admin-key"
ADMIN_USER_ID = 1001
USER_ID = 2001
OTHER_USER_ID = 2002
FALLBACK_URL = "postgresql://user:secret@localhost:5432/unused"


@pytest.fixture
def database_url() -> str:
    """Повернути URL тестової БД або пропустити тест, якщо його не задано."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL не задано")
    return url


@pytest.fixture
def settings() -> Settings:
    """Налаштування для тестів (без реального токена Telegram)."""
    return Settings(
        _env_file=None,
        database_url=os.environ.get("TEST_DATABASE_URL", FALLBACK_URL),
        admin_api_token=ADMIN_KEY,
        admin_platform_ids=[ADMIN_USER_ID],
        bot_polling_enabled=False,
    )


@pytest.fixture
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    """Рушій тестової БД; таблиці очищаються перед кожним тестом."""
    engine = create_async_engine(to_async_url(database_url), poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE processed_events, dialog_states, books, bot_users RESTART IDENTITY CASCADE"
            )
        )
    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Фабрика сесій тестової БД."""
    return create_session_factory(engine)


@pytest.fixture
def sender() -> FakeSender:
    """Підроблений відправник повідомлень."""
    return FakeSender()


@pytest.fixture
def handlers(
    session_factory: async_sessionmaker[AsyncSession], settings: Settings, sender: FakeSender
) -> BotHandlers:
    """Обробники бота поверх тестової БД."""
    return BotHandlers(session_factory, settings, sender)


@pytest.fixture
def chat(handlers: BotHandlers, sender: FakeSender) -> Chat:
    """Чат звичайного користувача."""
    return Chat(handlers, sender, USER_ID)


@pytest.fixture
def other_chat(handlers: BotHandlers, sender: FakeSender) -> Chat:
    """Чат іншого користувача."""
    return Chat(handlers, sender, OTHER_USER_ID)


@pytest.fixture
def admin_chat(handlers: BotHandlers, sender: FakeSender) -> Chat:
    """Чат адміністратора."""
    return Chat(handlers, sender, ADMIN_USER_ID)


@pytest.fixture
async def api_client(
    settings: Settings, session_factory: async_sessionmaker[AsyncSession]
) -> AsyncIterator[AsyncClient]:
    """HTTP-клієнт до FastAPI-застосунку з тестовою БД."""
    application = create_app()
    application.state.settings = settings
    application.state.session_factory = session_factory
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

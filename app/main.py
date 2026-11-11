"""Точка входу FastAPI: ініціалізація БД і запуск бота."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app._detail.constants import API_PREFIX
from app.api import admin, health
from app.bot.telegram_adapter import create_bot_runtime
from app.core.config import get_settings
from app.core.database import create_engine, create_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Підняти підключення до БД і (за налаштуванням) Telegram polling.

    Parameters
    ----------
    app : FastAPI
        Застосунок, у state якого кладуться налаштування та фабрика сесій.

    Yields
    ------
    None
        Керування на час роботи застосунку.
    """
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    app.state.settings = settings
    app.state.session_factory = session_factory
    runtime = (
        create_bot_runtime(settings, session_factory) if settings.bot_polling_enabled else None
    )
    if runtime is not None:
        runtime.start()
    try:
        yield
    finally:
        if runtime is not None:
            await runtime.stop()
        await engine.dispose()


def create_app() -> FastAPI:
    """Створити застосунок FastAPI.

    Returns
    -------
    FastAPI
        Застосунок із маршрутами /health і /api/v1/admin/stats.
    """
    application = FastAPI(title="Book Tracker Bot", version="1.0.0", lifespan=lifespan)
    application.include_router(health.router)
    application.include_router(admin.router, prefix=API_PREFIX)
    return application


app = create_app()

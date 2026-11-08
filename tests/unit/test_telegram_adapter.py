"""Модульні тести адаптера Telegram із підробленим Bot."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramNetworkError
from aiogram.methods import SendMessage

from app.bot import telegram_adapter
from app.bot.contracts import IncomingMessage
from app.bot.telegram_adapter import AiogramSender, BotRuntime, create_bot_runtime, on_message
from app.core.config import Settings
from app.core.exceptions import ConfigurationError, PlatformError

ADMIN_KEY = "adapter-test-key"
BOT_KEY = "123:fake"


async def hang(**_: object) -> None:
    """Імітувати запит, що ніколи не завершується."""
    await asyncio.sleep(5)


async def never_ending(*_: object, **__: object) -> None:
    """Імітувати нескінченний polling."""
    await asyncio.sleep(60)


async def test_sender_sends_message() -> None:
    """Успішна відправка викликає send_message."""
    bot = SimpleNamespace(send_message=AsyncMock())
    await AiogramSender(bot).send_text(5, "привіт")
    bot.send_message.assert_awaited_once_with(chat_id=5, text="привіт")


async def test_sender_wraps_telegram_error() -> None:
    """Помилка Telegram перетворюється на PlatformError."""
    error = TelegramNetworkError(method=SendMessage(chat_id=1, text="x"), message="мережа")
    bot = SimpleNamespace(send_message=AsyncMock(side_effect=error))
    with pytest.raises(PlatformError):
        await AiogramSender(bot).send_text(5, "привіт")


async def test_sender_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    """Перевищення тайм-ауту перетворюється на PlatformError."""
    monkeypatch.setattr(telegram_adapter, "PLATFORM_TIMEOUT_SECONDS", 0.01)
    bot = SimpleNamespace(send_message=hang)
    with pytest.raises(PlatformError):
        await AiogramSender(bot).send_text(5, "привіт")


async def test_on_message_converts_update() -> None:
    """update_id стає event_id, а дані користувача переносяться."""
    handlers = SimpleNamespace(handle_message=AsyncMock())
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=77, full_name="Іван Петренко"), text="/help"
    )
    await on_message(message, SimpleNamespace(update_id=900), handlers)
    handlers.handle_message.assert_awaited_once_with(
        IncomingMessage(event_id=900, platform_user_id=77, text="/help", display_name="Іван Петренко")
    )


async def test_on_message_ignores_messages_without_sender() -> None:
    """Повідомлення без відправника ігноруються."""
    handlers = SimpleNamespace(handle_message=AsyncMock())
    await on_message(SimpleNamespace(from_user=None, text="x"), SimpleNamespace(update_id=1), handlers)
    handlers.handle_message.assert_not_awaited()


def test_create_bot_runtime_requires_token() -> None:
    """Без BOT_TOKEN створення бота завершується помилкою конфігурації."""
    settings = Settings(_env_file=None, database_url="postgresql://x/y", admin_api_token=ADMIN_KEY)
    with pytest.raises(ConfigurationError):
        create_bot_runtime(settings, SimpleNamespace())


async def test_create_bot_runtime_builds_runtime() -> None:
    """З токеном створюється BotRuntime."""
    settings = Settings(
        _env_file=None, database_url="postgresql://x/y", admin_api_token=ADMIN_KEY, bot_token=BOT_KEY
    )
    runtime = create_bot_runtime(settings, SimpleNamespace())
    assert isinstance(runtime, BotRuntime)
    await runtime.stop()


async def test_runtime_start_and_stop() -> None:
    """Polling запускається у фоні й зупиняється без помилок."""
    bot = SimpleNamespace(session=SimpleNamespace(close=AsyncMock()))
    runtime = BotRuntime(bot, SimpleNamespace())
    runtime._dispatcher.start_polling = never_ending
    runtime.start()
    await asyncio.sleep(0)
    await runtime.stop()
    bot.session.close.assert_awaited_once()

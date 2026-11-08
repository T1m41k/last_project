"""Адаптер Telegram на aiogram 3 (long polling)."""

import asyncio
import contextlib

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message, Update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app._detail.constants import PLATFORM_TIMEOUT_SECONDS
from app.bot.contracts import IncomingMessage
from app.bot.handlers import BotHandlers
from app.core.config import Settings
from app.core.exceptions import ConfigurationError, PlatformError


class AiogramSender:
    """Відправник повідомлень через aiogram із тайм-аутом."""

    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def send_text(self, chat_id: int, text: str) -> None:
        """Надіслати текст у чат.

        Parameters
        ----------
        chat_id : int
            Ідентифікатор чату.
        text : str
            Текст повідомлення.

        Raises
        ------
        PlatformError
            Якщо Telegram повернув помилку або перевищено тайм-аут.
        """
        try:
            async with asyncio.timeout(PLATFORM_TIMEOUT_SECONDS):
                await self._bot.send_message(chat_id=chat_id, text=text)
        except (TelegramAPIError, TimeoutError) as error:
            raise PlatformError("Не вдалося надіслати повідомлення в Telegram") from error


async def on_message(message: Message, event_update: Update, handlers: BotHandlers) -> None:
    """Передати вхідне повідомлення Telegram у платформо-незалежні обробники.

    Parameters
    ----------
    message : Message
        Повідомлення aiogram.
    event_update : Update
        Оновлення; його update_id використовується як platform_event_id.
    handlers : BotHandlers
        Обробники, передані як workflow-дані диспетчера.
    """
    if message.from_user is None:
        return
    await handlers.handle_message(
        IncomingMessage(
            event_id=event_update.update_id,
            platform_user_id=message.from_user.id,
            text=message.text or "",
            display_name=message.from_user.full_name,
        )
    )


class BotRuntime:
    """Життєвий цикл long polling у фоновій задачі."""

    def __init__(self, bot: Bot, handlers: BotHandlers) -> None:
        self._bot = bot
        self._handlers = handlers
        self._dispatcher = Dispatcher()
        self._dispatcher.message.register(on_message)
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        """Запустити polling у фоновій задачі."""
        self._task = asyncio.create_task(
            self._dispatcher.start_polling(
                self._bot,
                handlers=self._handlers,
                handle_signals=False,
                close_bot_session=False,
                allowed_updates=["message"],
            )
        )

    async def stop(self) -> None:
        """Зупинити polling і закрити HTTP-сесію бота."""
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        await self._bot.session.close()


def create_bot_runtime(
    settings: Settings, session_factory: async_sessionmaker[AsyncSession]
) -> BotRuntime:
    """Створити бота з налаштувань.

    Parameters
    ----------
    settings : Settings
        Налаштування із BOT_TOKEN.
    session_factory : async_sessionmaker[AsyncSession]
        Фабрика сесій БД.

    Returns
    -------
    BotRuntime
        Готове до запуску середовище бота.

    Raises
    ------
    ConfigurationError
        Якщо BOT_TOKEN не задано.
    """
    if not settings.bot_token:
        raise ConfigurationError("BOT_TOKEN не задано, а BOT_POLLING_ENABLED=true")
    bot = Bot(token=settings.bot_token)
    return BotRuntime(bot, BotHandlers(session_factory, settings, AiogramSender(bot)))

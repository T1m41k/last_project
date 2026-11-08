"""Обробники повідомлень бота: маршрутизація команд і діалогів.

Модуль не містить SQL і не залежить від бібліотеки платформи: уся робота з
даними йде через сервіси, а відправка — через протокол MessageSender.
"""

import logging
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app._detail.bot.helpers import parse_command, truncate_message
from app._detail.constants import (
    CMD_ADD,
    CMD_BOOK,
    CMD_CANCEL,
    CMD_DELETE,
    CMD_HELP,
    CMD_LIST,
    CMD_START,
    CMD_STATS,
    CMD_UPDATE,
    COMMANDS_ALLOWED_IN_DIALOG,
    LIST_PAGE_SIZE,
    PLATFORM_TELEGRAM,
)
from app._detail.formatting.helpers import (
    format_book_details,
    format_book_line,
    format_book_list,
)
from app._detail.validation.helpers import parse_positive_int
from app.bot import texts
from app.bot.contracts import IncomingMessage, MessageSender
from app.core.config import Settings
from app.core.exceptions import AppError, PlatformError
from app.models import BotUser
from app.services.add_book_dialog_service import DialogOutcome
from app.services.container import Services, build_services

logger = logging.getLogger(__name__)

CommandHandler = Callable[[Services, BotUser, str], Awaitable[str]]


class BotHandlers:
    """Обробка вхідних повідомлень: дедуплікація, реєстрація, команди, діалоги."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings,
        sender: MessageSender,
    ) -> None:
        self._session_factory = session_factory
        self._admin_ids = frozenset(settings.admin_platform_ids)
        self._sender = sender
        self._commands: dict[str, CommandHandler] = {
            CMD_START: self._cmd_start,
            CMD_HELP: self._cmd_help,
            CMD_ADD: self._cmd_add,
            CMD_LIST: self._cmd_list,
            CMD_BOOK: self._cmd_book,
            CMD_UPDATE: self._cmd_update,
            CMD_DELETE: self._cmd_delete,
            CMD_CANCEL: self._cmd_cancel,
            CMD_STATS: self._cmd_stats,
        }

    async def handle_message(self, message: IncomingMessage) -> None:
        """Обробити повідомлення та надіслати відповідь.

        Дані фіксуються в БД до відправки відповіді, тому помилка або
        тайм-аут платформи не втрачає записи й не ламає обробку.

        Parameters
        ----------
        message : IncomingMessage
            Вхідне повідомлення.
        """
        try:
            reply = await self._process(message)
        except Exception:
            logger.exception("Не вдалося обробити подію %s", message.event_id)
            reply = texts.INTERNAL_ERROR
        if reply is not None:
            await self._send_reply(message.platform_user_id, reply)

    async def _process(self, message: IncomingMessage) -> str | None:
        """Виконати обробку в одній транзакції; None означає повторну подію."""
        async with self._session_factory() as session, session.begin():
            services = build_services(session)
            if not await services.events.claim(PLATFORM_TELEGRAM, message.event_id):
                return None
            user, _ = await services.users.register(message.platform_user_id, message.display_name)
            return await self._route(services, user, message.text)

    async def _route(self, services: Services, user: BotUser, text: str) -> str:
        """Спрямувати повідомлення на команду або крок діалогу."""
        parsed = parse_command(text)
        try:
            if parsed is None:
                return await self._handle_plain_text(services, user, text)
            return await self._handle_command(services, user, *parsed)
        except AppError as error:
            return str(error)

    async def _handle_plain_text(self, services: Services, user: BotUser, text: str) -> str:
        """Обробити не-команду: відповідь у діалозі або підказка."""
        state = await services.dialogs.get_active(user.id)
        if state is None:
            return texts.PLAIN_TEXT_HINT
        outcome = await services.add_book.answer(user.id, state, text)
        return self._render_outcome(outcome)

    async def _handle_command(
        self, services: Services, user: BotUser, name: str, args: str
    ) -> str:
        """Виконати команду з урахуванням активного діалогу."""
        handler = self._commands.get(name)
        if handler is None:
            return texts.UNKNOWN_COMMAND
        blocked = name not in COMMANDS_ALLOWED_IN_DIALOG
        if blocked and await services.dialogs.get_active(user.id) is not None:
            return texts.DIALOG_ACTIVE_REMINDER
        return await handler(services, user, args)

    @staticmethod
    def _render_outcome(outcome: DialogOutcome) -> str:
        """Перетворити результат кроку діалогу на текст відповіді."""
        if outcome.cancelled:
            return texts.CANCELLED
        if outcome.book is not None:
            return "Збережено!\n" + format_book_line(outcome.book)
        prefix = f"⚠️ {outcome.error}\n\n" if outcome.error else ""
        return prefix + texts.step_prompt(outcome.step, outcome.data)

    async def _cmd_start(self, services: Services, user: BotUser, args: str) -> str:
        """Привітати користувача (реєстрація вже виконана)."""
        return texts.WELCOME

    async def _cmd_help(self, services: Services, user: BotUser, args: str) -> str:
        """Показати довідку."""
        return texts.HELP

    async def _cmd_add(self, services: Services, user: BotUser, args: str) -> str:
        """Розпочати діалог додавання книги."""
        return self._render_outcome(await services.add_book.start(user.id))

    async def _cmd_list(self, services: Services, user: BotUser, args: str) -> str:
        """Показати сторінку списку власних книг."""
        page = parse_positive_int(args or "1", field_label="сторінка")
        books, total = await services.books.list_page(
            user.id, limit=LIST_PAGE_SIZE, offset=(page - 1) * LIST_PAGE_SIZE
        )
        if total == 0:
            return texts.LIST_EMPTY
        if not books:
            return texts.LIST_PAGE_EMPTY
        return format_book_list(books, page, total)

    async def _cmd_book(self, services: Services, user: BotUser, args: str) -> str:
        """Показати деталі книги."""
        if not args:
            return texts.USAGE_BOOK
        book = await services.books.get(user.id, parse_positive_int(args, field_label="id"))
        return format_book_details(book)

    async def _cmd_update(self, services: Services, user: BotUser, args: str) -> str:
        """Оновити поле власної книги."""
        parts = args.split(maxsplit=2)
        if len(parts) < 3:
            return texts.USAGE_UPDATE
        book_id = parse_positive_int(parts[0], field_label="id")
        book = await services.books.update_field(user.id, book_id, parts[1], parts[2])
        return "Оновлено.\n" + format_book_details(book)

    async def _cmd_delete(self, services: Services, user: BotUser, args: str) -> str:
        """Видалити власну книгу."""
        if not args:
            return texts.USAGE_DELETE
        book_id = parse_positive_int(args, field_label="id")
        await services.books.delete(user.id, book_id)
        return f"Запис #{book_id} видалено."

    async def _cmd_cancel(self, services: Services, user: BotUser, args: str) -> str:
        """Скасувати незавершений діалог."""
        if await services.dialogs.cancel(user.id):
            return texts.CANCELLED
        return texts.NOTHING_TO_CANCEL

    async def _cmd_stats(self, services: Services, user: BotUser, args: str) -> str:
        """Показати статистику; доступ визначає серверний ADMIN_PLATFORM_IDS."""
        if user.platform_user_id not in self._admin_ids:
            return texts.ACCESS_DENIED
        stats = await services.stats.collect()
        return f"Користувачів: {stats.users_count}\nЗаписів: {stats.books_count}"

    async def _send_reply(self, chat_id: int, reply: str) -> None:
        """Надіслати відповідь, не пропускаючи помилки платформи далі."""
        try:
            await self._sender.send_text(chat_id, truncate_message(reply))
        except (PlatformError, TimeoutError):
            logger.warning("Не вдалося надіслати відповідь у чат %s", chat_id, exc_info=True)

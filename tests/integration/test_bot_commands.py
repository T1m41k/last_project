"""Інтеграційні тести команд бота (потребують PostgreSQL)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app._detail.constants import LIST_PAGE_SIZE
from app.bot.contracts import IncomingMessage
from app.bot.handlers import BotHandlers
from app.core.config import Settings
from app.core.exceptions import PlatformError
from app.repositories.book_repository import BookRepository
from app.repositories.dialog_repository import DialogRepository
from app.repositories.user_repository import UserRepository
from app.services.container import build_services
from tests.conftest import USER_ID
from tests.support import Chat, FakeSender, next_event_id


async def add_book(chat: Chat, title: str = "Дюна", author: str = "Герберт", pages: str = "600") -> str:
    """Пройти діалог /add до кінця й повернути відповідь на підтвердження."""
    await chat.say("/add")
    await chat.say(title)
    await chat.say(author)
    await chat.say(pages)
    return await chat.say("так")


async def count_books(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Порахувати всі книги в БД."""
    async with session_factory() as session:
        return await BookRepository(session).count_all()


async def test_start_registers_user_by_platform_id(
    chat: Chat, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """/start реєструє користувача за platform_user_id один раз."""
    assert "Доступні команди" in await chat.say("/start")
    await chat.say("/start")
    async with session_factory() as session:
        users = UserRepository(session)
        user = await users.get_by_platform_id(USER_ID)
        assert user is not None and user.display_name == "Тест Користувач"
        assert await users.count() == 1


async def test_help_unknown_command_and_plain_text(chat: Chat) -> None:
    """/help, невідома команда та звичайний текст поза діалогом."""
    assert "/add" in await chat.say("/help")
    assert "Невідома команда" in await chat.say("/foo")
    assert "лише команди" in await chat.say("привіт")


async def test_full_crud_scenario(chat: Chat, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Повний CRUD: створення, список, деталі, оновлення, видалення."""
    assert "Збережено" in await add_book(chat)
    assert "Дюна — Герберт" in await chat.say("/list")
    assert "Сторінок: 600" in await chat.say("/book 1")
    assert "Статус: прочитано" in await chat.say("/update 1 status finished")
    assert "Статус: прочитано" in await chat.say("/book 1")
    assert "Нотатка: класика" in await chat.say("/update 1 note класика")
    assert "видалено" in await chat.say("/delete 1")
    assert "не знайдено" in await chat.say("/book 1")
    assert "ще немає книг" in await chat.say("/list")
    assert await count_books(session_factory) == 0


async def test_dialog_rejects_invalid_input_and_keeps_step(chat: Chat) -> None:
    """Невалідні відповіді в діалозі не просувають його вперед."""
    await chat.say("/add")
    assert "задовге" in await chat.say("а" * 201)
    await chat.say("Назва")
    await chat.say("Автор")
    assert "цілим числом" in await chat.say("багато")
    assert "від 1 до 10000" in await chat.say("0")
    assert "Перевірте дані" in await chat.say("250")
    assert "«так» або «ні»" in await chat.say("можливо")


async def test_dialog_decline_and_cancel(
    chat: Chat, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Відповідь «ні» та /cancel скасовують діалог без запису."""
    await chat.say("/add")
    await chat.say("Назва")
    await chat.say("Автор")
    await chat.say("100")
    assert "скасовано" in await chat.say("ні")
    await chat.say("/add")
    assert "скасовано" in await chat.say("/cancel")
    assert "Немає активного діалогу" in await chat.say("/cancel")
    assert await count_books(session_factory) == 0
    async with session_factory() as session:
        user = await UserRepository(session).get_by_platform_id(USER_ID)
        assert user is not None
        assert await DialogRepository(session).get(user.id) is None


async def test_commands_blocked_during_dialog(chat: Chat) -> None:
    """Під час діалогу інші команди просять його завершити; /help працює."""
    await chat.say("/add")
    assert "/cancel" in await chat.say("/list")
    assert "Доступні команди" in await chat.say("/help")


async def test_dialog_state_survives_restart(
    session_factory: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    """Дані, введені до перезапуску, потрапляють у збережену книгу."""
    sender_before, sender_after = FakeSender(), FakeSender()
    before = Chat(BotHandlers(session_factory, settings, sender_before), sender_before, USER_ID)
    await before.say("/add")
    await before.say("Дюна")
    await before.say("Герберт")
    after = Chat(BotHandlers(session_factory, settings, sender_after), sender_after, USER_ID)
    assert "Перевірте дані" in await after.say("600")
    assert "Збережено" in await after.say("так")
    assert "Дюна — Герберт (600 с.)" in await after.say("/list")


async def test_users_see_only_their_own_data(chat: Chat, other_chat: Chat) -> None:
    """Ізоляція: чужі записи недоступні для читання, зміни та видалення."""
    await add_book(chat)
    assert "ще немає книг" in await other_chat.say("/list")
    assert "не знайдено" in await other_chat.say("/book 1")
    assert "не знайдено" in await other_chat.say("/update 1 title Злам")
    assert "не знайдено" in await other_chat.say("/delete 1")
    assert "Назва: Дюна" in await chat.say("/book 1")


async def test_dialogs_are_isolated_between_users(chat: Chat, other_chat: Chat) -> None:
    """Діалог одного користувача не впливає на іншого."""
    await chat.say("/add")
    assert "лише команди" in await other_chat.say("випадковий текст")
    assert "ще немає книг" in await other_chat.say("/list")


async def test_command_argument_validation(chat: Chat) -> None:
    """Перевірка аргументів команд."""
    assert "Використання: /book" in await chat.say("/book")
    assert "Використання: /delete" in await chat.say("/delete")
    assert "Використання: /update" in await chat.say("/update 1 title")
    assert "додатним цілим" in await chat.say("/book abc")
    assert "додатним цілим" in await chat.say("/list 0")
    await add_book(chat)
    assert "Невідоме поле" in await chat.say("/update 1 колір синій")
    assert "цілим числом" in await chat.say("/update 1 pages багато")
    assert "Невідомий статус" in await chat.say("/update 1 status щось")


async def test_list_is_paged(
    chat: Chat, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Список розбивається на сторінки, найновіші першими."""
    await chat.say("/start")
    async with session_factory() as session, session.begin():
        services = build_services(session)
        user, _ = await services.users.register(USER_ID, None)
        for index in range(LIST_PAGE_SIZE + 2):
            await services.books.create(user.id, title=f"Книга {index}", author="А", pages=10)
    first = await chat.say("/list")
    assert "Книга 11" in first and "/list 2" in first and "Книга 1 " not in first
    second = await chat.say("/list 2")
    assert "Книга 1 " in second and "/list 3" not in second
    assert "немає записів" in await chat.say("/list 9")


async def test_duplicate_event_does_not_duplicate_record(
    handlers: BotHandlers, sender: FakeSender, chat: Chat, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Повторно отримана подія підтвердження не створює другий запис."""
    await chat.say("/add")
    await chat.say("Дюна")
    await chat.say("Герберт")
    await chat.say("600")
    confirm = IncomingMessage(event_id=next_event_id(), platform_user_id=USER_ID, text="так")
    await handlers.handle_message(confirm)
    replies_before = len(sender.sent)
    await handlers.handle_message(confirm)
    assert len(sender.sent) == replies_before
    assert await count_books(session_factory) == 1


async def test_admin_stats_only_for_configured_admins(
    chat: Chat, admin_chat: Chat, other_chat: Chat
) -> None:
    """Статистика доступна лише ідентифікаторам із ADMIN_PLATFORM_IDS."""
    await add_book(chat)
    await other_chat.say("/start")
    assert "лише адміністраторам" in await chat.say("/stats")
    stats = await admin_chat.say("/stats")
    assert "Користувачів: 3" in stats and "Записів: 1" in stats


async def test_platform_errors_do_not_lose_data(
    chat: Chat, sender: FakeSender, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Помилка чи тайм-аут Telegram не ламає обробку і не втрачає запис."""
    await chat.say("/add")
    await chat.say("Дюна")
    await chat.say("Герберт")
    await chat.say("600")
    sender.error = TimeoutError()
    await chat._handlers.handle_message(
        IncomingMessage(event_id=next_event_id(), platform_user_id=USER_ID, text="так")
    )
    assert await count_books(session_factory) == 1
    sender.error = PlatformError("збій")
    await chat._handlers.handle_message(
        IncomingMessage(event_id=next_event_id(), platform_user_id=USER_ID, text="/list")
    )
    sender.error = None
    assert "Дюна" in await chat.say("/list")


async def broken_process(*_: object, **__: object) -> None:
    """Імітувати неочікуваний збій обробки."""
    raise RuntimeError("секретна деталь")


async def test_internal_error_returns_generic_reply(
    handlers: BotHandlers, sender: FakeSender, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Неочікувана помилка дає загальну відповідь без внутрішніх деталей."""
    monkeypatch.setattr(BotHandlers, "_process", broken_process)
    await handlers.handle_message(
        IncomingMessage(event_id=next_event_id(), platform_user_id=USER_ID, text="/help")
    )
    text = sender.last_text(USER_ID)
    assert "внутрішня помилка" in text
    assert "секретна" not in text

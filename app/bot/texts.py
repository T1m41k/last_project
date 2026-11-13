"""Тексти відповідей бота."""

from collections.abc import Mapping
from typing import Any

from app._detail.constants import (
    BOOK_AUTHOR_MAX_LENGTH,
    BOOK_MAX_PAGES,
    BOOK_MIN_PAGES,
    BOOK_TITLE_MAX_LENGTH,
    STEP_AUTHOR,
    STEP_CONFIRM,
    STEP_PAGES,
    STEP_TITLE,
)
from app._detail.formatting.helpers import format_summary

HELP = (
    "Доступні команди:\n"
    "/add — додати книгу (покроковий діалог)\n"
    "/list [сторінка] — список ваших книг\n"
    "/book <id> — докладно про книгу\n"
    "/update <id> <поле> <значення> — змінити поле "
    "(title, author, pages, status, note; «-» очищає note)\n"
    "/delete <id> — видалити книгу\n"
    "/cancel — скасувати поточний діалог\n"
    "/help — ця довідка"
)
WELCOME = (
    "Привіт! Я бот для обліку прочитаних і запланованих книг. "
    "Ви бачите й змінюєте лише власні записи.\n\n" + HELP
)
UNKNOWN_COMMAND = "Невідома команда. Список команд: /help"
PLAIN_TEXT_HINT = "Я розумію лише команди. Список команд: /help"
DIALOG_ACTIVE_REMINDER = "Спершу завершіть поточний діалог або скасуйте його командою /cancel."
CANCELLED = "Діалог скасовано."
NOTHING_TO_CANCEL = "Немає активного діалогу."
ACCESS_DENIED = "Ця команда доступна лише адміністраторам."
LIST_EMPTY = "У вас ще немає книг. Додайте першу: /add"
LIST_PAGE_EMPTY = "На цій сторінці немає записів. Почніть з /list"
INTERNAL_ERROR = "Сталася внутрішня помилка. Спробуйте ще раз пізніше."
USAGE_BOOK = "Використання: /book <id>"
USAGE_DELETE = "Використання: /delete <id>"
USAGE_UPDATE = "Використання: /update <id> <поле> <значення>, напр. /update 3 status finished"
STEP_PROMPTS = {
    STEP_TITLE: f"Крок 1/3. Введіть назву книги (до {BOOK_TITLE_MAX_LENGTH} символів).",
    STEP_AUTHOR: f"Крок 2/3. Введіть автора (до {BOOK_AUTHOR_MAX_LENGTH} символів).",
    STEP_PAGES: f"Крок 3/3. Введіть кількість сторінок ({BOOK_MIN_PAGES}–{BOOK_MAX_PAGES}).",
}
CANCEL_FOOTER = "\n\n/cancel — скасувати діалог."


def step_prompt(step: str, data: Mapping[str, Any]) -> str:
    """Сформувати запит для кроку діалогу.

    Parameters
    ----------
    step : str
        Код кроку.
    data : Mapping[str, Any]
        Зібрані дані (для підсумку на кроці підтвердження).

    Returns
    -------
    str
        Текст запиту.
    """
    if step == STEP_CONFIRM:
        return (
            "Перевірте дані:\n"
            + format_summary(data)
            + "\n\nЗберегти? Відповідайте «так» або «ні»."
            + CANCEL_FOOTER
        )
    return STEP_PROMPTS.get(step, "Невідомий крок.") + CANCEL_FOOTER

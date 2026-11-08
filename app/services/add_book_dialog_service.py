"""Діалог додавання книги: збір даних, підсумок, підтвердження, запис."""

from dataclasses import dataclass, field
from typing import Any

from app._detail.bot.helpers import is_no, is_yes
from app._detail.constants import (
    BOOK_AUTHOR_MAX_LENGTH,
    BOOK_TITLE_MAX_LENGTH,
    DIALOG_FLOW_ADD_BOOK,
    NEXT_STEP,
    STEP_AUTHOR,
    STEP_CONFIRM,
    STEP_PAGES,
    STEP_TITLE,
)
from app._detail.validation.helpers import normalize_text, parse_pages
from app.core.exceptions import ValidationFailedError
from app.models import Book, DialogState
from app.services.book_service import BookService
from app.services.dialog_service import DialogService


@dataclass(frozen=True)
class DialogOutcome:
    """Результат кроку діалогу."""

    step: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    book: Book | None = None
    cancelled: bool = False


class AddBookDialogService:
    """Покроковий діалог створення книги зі станом у БД."""

    def __init__(self, dialogs: DialogService, books: BookService) -> None:
        self._dialogs = dialogs
        self._books = books

    async def start(self, user_id: int) -> DialogOutcome:
        """Розпочати діалог із першого кроку.

        Parameters
        ----------
        user_id : int
            Внутрішній id користувача.

        Returns
        -------
        DialogOutcome
            Перший крок (введення назви).
        """
        await self._dialogs.start(user_id, DIALOG_FLOW_ADD_BOOK, STEP_TITLE)
        return DialogOutcome(step=STEP_TITLE)

    async def answer(self, user_id: int, state: DialogState, text: str) -> DialogOutcome:
        """Обробити відповідь користувача на поточному кроці.

        Parameters
        ----------
        user_id : int
            Внутрішній id користувача.
        state : DialogState
            Поточний стан діалогу.
        text : str
            Відповідь користувача.

        Returns
        -------
        DialogOutcome
            Наступний крок, помилка валідації, збережена книга або скасування.
        """
        data = dict(state.data)
        if state.step == STEP_CONFIRM:
            return await self._confirm(user_id, data, text)
        try:
            data[state.step] = self._parse_answer(state.step, text)
        except ValidationFailedError as error:
            return DialogOutcome(step=state.step, data=data, error=str(error))
        next_step = NEXT_STEP[state.step]
        await self._dialogs.advance(state, next_step, data)
        return DialogOutcome(step=next_step, data=data)

    async def _confirm(self, user_id: int, data: dict[str, Any], text: str) -> DialogOutcome:
        """Обробити відповідь на запит підтвердження."""
        if is_yes(text):
            book = await self._books.create(
                user_id, title=data["title"], author=data["author"], pages=data["pages"]
            )
            await self._dialogs.cancel(user_id)
            return DialogOutcome(step=STEP_CONFIRM, data=data, book=book)
        if is_no(text):
            await self._dialogs.cancel(user_id)
            return DialogOutcome(step=STEP_CONFIRM, data=data, cancelled=True)
        return DialogOutcome(step=STEP_CONFIRM, data=data, error="Відповідайте «так» або «ні».")

    @staticmethod
    def _parse_answer(step: str, text: str) -> str | int:
        """Розібрати відповідь відповідно до кроку."""
        if step == STEP_TITLE:
            return normalize_text(text, field_label="назва", max_length=BOOK_TITLE_MAX_LENGTH)
        if step == STEP_AUTHOR:
            return normalize_text(text, field_label="автор", max_length=BOOK_AUTHOR_MAX_LENGTH)
        if step == STEP_PAGES:
            return parse_pages(text)
        raise ValidationFailedError("Невідомий крок діалогу. Скасуйте його командою /cancel.")

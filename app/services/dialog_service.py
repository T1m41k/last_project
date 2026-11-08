"""Сервіс збереження стану діалогів у PostgreSQL."""

from typing import Any

from app.models import DialogState
from app.repositories.dialog_repository import DialogRepository


class DialogService:
    """Керування станом багатокрокових діалогів."""

    def __init__(self, dialogs: DialogRepository) -> None:
        self._dialogs = dialogs

    async def get_active(self, user_id: int) -> DialogState | None:
        """Отримати незавершений діалог.

        Parameters
        ----------
        user_id : int
            Внутрішній id користувача.

        Returns
        -------
        DialogState | None
            Стан діалогу або None.
        """
        return await self._dialogs.get(user_id)

    async def start(self, user_id: int, flow: str, step: str) -> DialogState:
        """Розпочати діалог, замінивши попередній.

        Parameters
        ----------
        user_id : int
            Внутрішній id користувача.
        flow : str
            Код сценарію.
        step : str
            Перший крок.

        Returns
        -------
        DialogState
            Новий стан.
        """
        return await self._dialogs.save(user_id, flow, step, {})

    async def advance(self, state: DialogState, step: str, data: dict[str, Any]) -> DialogState:
        """Перейти до наступного кроку зі збереженням даних.

        Parameters
        ----------
        state : DialogState
            Поточний стан.
        step : str
            Наступний крок.
        data : dict[str, Any]
            Зібрані дані.

        Returns
        -------
        DialogState
            Оновлений стан.
        """
        return await self._dialogs.save(state.user_id, state.flow, step, data)

    async def cancel(self, user_id: int) -> bool:
        """Скасувати або завершити діалог.

        Parameters
        ----------
        user_id : int
            Внутрішній id користувача.

        Returns
        -------
        bool
            True, якщо діалог існував.
        """
        return await self._dialogs.delete_for_user(user_id)

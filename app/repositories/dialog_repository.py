"""Репозиторій станів діалогів."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DialogState


class DialogRepository:
    """Запити до таблиці dialog_states (один діалог на користувача)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: int) -> DialogState | None:
        """Отримати активний діалог користувача.

        Parameters
        ----------
        user_id : int
            Внутрішній id користувача.

        Returns
        -------
        DialogState | None
            Стан діалогу або None.
        """
        result = await self._session.execute(
            select(DialogState).where(DialogState.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def save(
        self, user_id: int, flow: str, step: str, data: dict[str, Any]
    ) -> DialogState:
        """Створити або оновити стан діалогу.

        Parameters
        ----------
        user_id : int
            Внутрішній id користувача.
        flow : str
            Код сценарію.
        step : str
            Поточний крок.
        data : dict[str, Any]
            Зібрані дані.

        Returns
        -------
        DialogState
            Збережений стан.
        """
        state = await self.get(user_id)
        if state is None:
            state = DialogState(user_id=user_id, flow=flow, step=step, data=data)
            self._session.add(state)
        else:
            state.flow = flow
            state.step = step
            state.data = data
        await self._session.flush()
        return state

    async def delete_for_user(self, user_id: int) -> bool:
        """Видалити діалог користувача.

        Parameters
        ----------
        user_id : int
            Внутрішній id користувача.

        Returns
        -------
        bool
            True, якщо діалог існував.
        """
        state = await self.get(user_id)
        if state is None:
            return False
        await self._session.delete(state)
        await self._session.flush()
        return True

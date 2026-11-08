"""Сервіс користувачів бота."""

from app._detail.constants import DISPLAY_NAME_MAX_LENGTH
from app.models import BotUser
from app.repositories.user_repository import UserRepository


class UserService:
    """Реєстрація користувачів за platform_user_id."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def register(
        self, platform_user_id: int, display_name: str | None
    ) -> tuple[BotUser, bool]:
        """Повернути користувача, зареєструвавши його при першому зверненні.

        Parameters
        ----------
        platform_user_id : int
            Незмінний ідентифікатор на платформі (нікнейм не використовується).
        display_name : str | None
            Відображуване ім'я; обрізається до допустимої довжини.

        Returns
        -------
        tuple[BotUser, bool]
            Користувач і ознака, що його щойно створено.
        """
        name = (display_name or "").strip()[:DISPLAY_NAME_MAX_LENGTH] or None
        return await self._users.get_or_create(platform_user_id, name)

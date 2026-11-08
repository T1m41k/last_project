"""Репозиторій користувачів бота."""

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BotUser


class UserRepository:
    """Запити до таблиці bot_users."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_platform_id(self, platform_user_id: int) -> BotUser | None:
        """Знайти користувача за ідентифікатором платформи.

        Parameters
        ----------
        platform_user_id : int
            Незмінний ідентифікатор користувача на платформі.

        Returns
        -------
        BotUser | None
            Користувач або None.
        """
        result = await self._session.execute(
            select(BotUser).where(BotUser.platform_user_id == platform_user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self, platform_user_id: int, display_name: str | None
    ) -> tuple[BotUser, bool]:
        """Повернути користувача, створивши його за потреби.

        Створення атомарне (INSERT ... ON CONFLICT DO NOTHING), тому гонка
        двох одночасних повідомлень не створює дублікатів.

        Parameters
        ----------
        platform_user_id : int
            Незмінний ідентифікатор користувача на платформі.
        display_name : str | None
            Відображуване ім'я (не є ідентифікатором).

        Returns
        -------
        tuple[BotUser, bool]
            Користувач і ознака, що його щойно створено.

        Raises
        ------
        RuntimeError
            Якщо користувача не вдалося знайти після вставки.
        """
        statement = (
            insert(BotUser)
            .values(platform_user_id=platform_user_id, display_name=display_name)
            .on_conflict_do_nothing(index_elements=["platform_user_id"])
            .returning(BotUser.id)
        )
        created = (await self._session.execute(statement)).scalar_one_or_none() is not None
        user = await self.get_by_platform_id(platform_user_id)
        if user is None:
            raise RuntimeError("Користувача не знайдено після вставки")
        return user, created

    async def count(self) -> int:
        """Порахувати користувачів.

        Returns
        -------
        int
            Кількість користувачів.
        """
        result = await self._session.execute(select(func.count()).select_from(BotUser))
        return result.scalar_one()

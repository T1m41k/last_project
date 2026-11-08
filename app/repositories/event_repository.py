"""Репозиторій оброблених подій платформи."""

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProcessedEvent


class EventRepository:
    """Запити до таблиці processed_events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def claim(self, platform: str, platform_event_id: int) -> bool:
        """Зафіксувати подію як оброблювану.

        Parameters
        ----------
        platform : str
            Код платформи.
        platform_event_id : int
            Ідентифікатор події на платформі.

        Returns
        -------
        bool
            True, якщо подію зафіксовано вперше; False, якщо це повтор.
        """
        statement = (
            insert(ProcessedEvent)
            .values(platform=platform, platform_event_id=platform_event_id)
            .on_conflict_do_nothing(index_elements=["platform", "platform_event_id"])
            .returning(ProcessedEvent.id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none() is not None

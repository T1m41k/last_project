"""Сервіс ідемпотентності подій платформи."""

from app.repositories.event_repository import EventRepository


class EventService:
    """Відсікання повторно отриманих подій."""

    def __init__(self, events: EventRepository) -> None:
        self._events = events

    async def claim(self, platform: str, platform_event_id: int) -> bool:
        """Зареєструвати подію; повтор повертає False.

        Parameters
        ----------
        platform : str
            Код платформи.
        platform_event_id : int
            Ідентифікатор події на платформі.

        Returns
        -------
        bool
            True, якщо подію ще не оброблено.
        """
        return await self._events.claim(platform, platform_event_id)

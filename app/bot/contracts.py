"""Незалежні від платформи типи для бота."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class IncomingMessage:
    """Вхідне текстове повідомлення користувача."""

    event_id: int
    platform_user_id: int
    text: str
    display_name: str | None = None


class MessageSender(Protocol):
    """Відправник повідомлень; у тестах замінюється підробкою."""

    async def send_text(self, chat_id: int, text: str) -> None:
        """Надіслати текст у чат.

        Parameters
        ----------
        chat_id : int
            Ідентифікатор чату (для приватних чатів збігається з id користувача).
        text : str
            Текст повідомлення.
        """

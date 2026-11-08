"""Допоміжні функції розбору повідомлень бота."""

from app._detail.constants import MAX_MESSAGE_LENGTH, NO_ANSWERS, YES_ANSWERS


def parse_command(text: str) -> tuple[str, str] | None:
    """Розібрати текст на назву команди й аргументи.

    Parameters
    ----------
    text : str
        Текст повідомлення.

    Returns
    -------
    tuple[str, str] | None
        Пара (назва без «/» і без суфікса @bot, аргументи) або None,
        якщо повідомлення не є командою.
    """
    stripped = text.strip()
    if not stripped.startswith("/"):
        return None
    parts = stripped[1:].split(maxsplit=1)
    if not parts:
        return "", ""
    name = parts[0].split("@", 1)[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""
    return name, args


def is_yes(text: str) -> bool:
    """Перевірити, чи є відповідь ствердною.

    Parameters
    ----------
    text : str
        Відповідь користувача.

    Returns
    -------
    bool
        True для «так», «yes» тощо.
    """
    return text.strip().lower() in YES_ANSWERS


def is_no(text: str) -> bool:
    """Перевірити, чи є відповідь заперечною.

    Parameters
    ----------
    text : str
        Відповідь користувача.

    Returns
    -------
    bool
        True для «ні», «no» тощо.
    """
    return text.strip().lower() in NO_ANSWERS


def truncate_message(text: str) -> str:
    """Обрізати відповідь до ліміту довжини повідомлення платформи.

    Parameters
    ----------
    text : str
        Текст відповіді.

    Returns
    -------
    str
        Текст, не довший за MAX_MESSAGE_LENGTH.
    """
    if len(text) <= MAX_MESSAGE_LENGTH:
        return text
    return text[: MAX_MESSAGE_LENGTH - 1] + "…"

"""Допоміжні функції валідації введених користувачем значень."""

from app._detail.constants import (
    BOOK_MAX_PAGES,
    BOOK_MIN_PAGES,
    BOOK_NOTE_MAX_LENGTH,
    CLEAR_NOTE_MARKER,
    FIELD_ALIASES,
    STATUS_ALIASES,
)
from app.core.exceptions import ValidationFailedError


def normalize_text(value: str, *, field_label: str, max_length: int) -> str:
    """Прибрати зайві пробіли та перевірити довжину тексту.

    Parameters
    ----------
    value : str
        Введений користувачем текст.
    field_label : str
        Назва поля для повідомлення про помилку.
    max_length : int
        Максимально допустима кількість символів.

    Returns
    -------
    str
        Нормалізований непорожній текст.

    Raises
    ------
    ValidationFailedError
        Якщо текст порожній або задовгий.
    """
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValidationFailedError(f"Поле «{field_label}» не може бути порожнім.")
    if len(cleaned) > max_length:
        raise ValidationFailedError(
            f"Поле «{field_label}» задовге: максимум {max_length} символів."
        )
    return cleaned


def ensure_pages_in_range(pages: int) -> int:
    """Перевірити, що кількість сторінок у дозволеному діапазоні.

    Parameters
    ----------
    pages : int
        Кількість сторінок.

    Returns
    -------
    int
        Те саме значення, якщо воно коректне.

    Raises
    ------
    ValidationFailedError
        Якщо значення поза діапазоном.
    """
    if not BOOK_MIN_PAGES <= pages <= BOOK_MAX_PAGES:
        raise ValidationFailedError(
            f"Кількість сторінок має бути від {BOOK_MIN_PAGES} до {BOOK_MAX_PAGES}."
        )
    return pages


def parse_pages(value: str) -> int:
    """Перетворити текст на кількість сторінок.

    Parameters
    ----------
    value : str
        Введений текст.

    Returns
    -------
    int
        Кількість сторінок.

    Raises
    ------
    ValidationFailedError
        Якщо текст не є цілим числом або число поза діапазоном.
    """
    cleaned = value.strip()
    if not (cleaned.isascii() and cleaned.isdecimal()):
        raise ValidationFailedError("Кількість сторінок має бути цілим числом.")
    return ensure_pages_in_range(int(cleaned))


def parse_positive_int(value: str, *, field_label: str) -> int:
    """Перетворити текст на додатне ціле число.

    Parameters
    ----------
    value : str
        Введений текст.
    field_label : str
        Назва поля для повідомлення про помилку.

    Returns
    -------
    int
        Додатне ціле число.

    Raises
    ------
    ValidationFailedError
        Якщо текст не є додатним цілим числом.
    """
    cleaned = value.strip()
    if not (cleaned.isascii() and cleaned.isdecimal()) or int(cleaned) < 1:
        raise ValidationFailedError(f"«{field_label}» має бути додатним цілим числом.")
    return int(cleaned)


def parse_status(value: str) -> str:
    """Перетворити текст на код статусу книги.

    Parameters
    ----------
    value : str
        Код або українська назва статусу.

    Returns
    -------
    str
        Канонічний код статусу.

    Raises
    ------
    ValidationFailedError
        Якщо статус невідомий.
    """
    status = STATUS_ALIASES.get(value.strip().lower())
    if status is None:
        raise ValidationFailedError(
            "Невідомий статус. Допустимі: planned (заплановано), reading (читаю), "
            "finished (прочитано)."
        )
    return status


def parse_field_name(value: str) -> str:
    """Перетворити назву поля (англійську чи українську) на канонічну.

    Parameters
    ----------
    value : str
        Назва поля, введена користувачем.

    Returns
    -------
    str
        Канонічна назва поля.

    Raises
    ------
    ValidationFailedError
        Якщо поле невідоме.
    """
    field = FIELD_ALIASES.get(value.strip().lower())
    if field is None:
        raise ValidationFailedError("Невідоме поле. Допустимі: title, author, pages, status, note.")
    return field


def parse_note(value: str) -> str | None:
    """Розібрати нотатку; символ «-» очищає її.

    Parameters
    ----------
    value : str
        Введений текст.

    Returns
    -------
    str | None
        Нормалізована нотатка або None, якщо її очищено.
    """
    if value.strip() == CLEAR_NOTE_MARKER:
        return None
    return normalize_text(value, field_label="нотатка", max_length=BOOK_NOTE_MAX_LENGTH)

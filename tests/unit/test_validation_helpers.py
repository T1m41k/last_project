"""Модульні тести допоміжних функцій валідації."""

import pytest

from app._detail.validation.helpers import (
    ensure_pages_in_range,
    normalize_text,
    parse_field_name,
    parse_note,
    parse_pages,
    parse_positive_int,
    parse_status,
)
from app.core.exceptions import ValidationFailedError


def test_normalize_text_collapses_whitespace() -> None:
    """Зайві пробіли прибираються."""
    assert (
        normalize_text("  Дюна   Герберта ", field_label="назва", max_length=50) == "Дюна Герберта"
    )


def test_normalize_text_rejects_empty() -> None:
    """Порожній текст відхиляється."""
    with pytest.raises(ValidationFailedError):
        normalize_text("   ", field_label="назва", max_length=50)


def test_normalize_text_rejects_too_long() -> None:
    """Задовгий текст відхиляється."""
    with pytest.raises(ValidationFailedError, match="максимум 5"):
        normalize_text("абвгде", field_label="назва", max_length=5)


@pytest.mark.parametrize(("raw", "expected"), [("1", 1), (" 320 ", 320), ("10000", 10000)])
def test_parse_pages_accepts_valid(raw: str, expected: int) -> None:
    """Коректна кількість сторінок приймається."""
    assert parse_pages(raw) == expected


@pytest.mark.parametrize("raw", ["0", "10001", "abc", "-5", "3.5", "", "²"])
def test_parse_pages_rejects_invalid(raw: str) -> None:
    """Некоректна кількість сторінок відхиляється."""
    with pytest.raises(ValidationFailedError):
        parse_pages(raw)


def test_ensure_pages_in_range_rejects_zero() -> None:
    """Нуль сторінок неприпустимий."""
    with pytest.raises(ValidationFailedError):
        ensure_pages_in_range(0)


def test_parse_positive_int() -> None:
    """Додатні цілі приймаються, решта відхиляється."""
    assert parse_positive_int("7", field_label="id") == 7
    for raw in ("0", "x", "-1", ""):
        with pytest.raises(ValidationFailedError):
            parse_positive_int(raw, field_label="id")


def test_parse_status_accepts_aliases() -> None:
    """Статус розпізнається англійською та українською."""
    assert parse_status("FINISHED") == "finished"
    assert parse_status("читаю") == "reading"
    with pytest.raises(ValidationFailedError):
        parse_status("щось")


def test_parse_field_name() -> None:
    """Назви полів розпізнаються з аліасами."""
    assert parse_field_name("Назва") == "title"
    assert parse_field_name("pages") == "pages"
    with pytest.raises(ValidationFailedError):
        parse_field_name("колір")


def test_parse_note_clears_with_dash() -> None:
    """Символ «-» очищає нотатку."""
    assert parse_note("-") is None
    assert parse_note(" цікаво ") == "цікаво"

"""Тести pre-commit hook перевірки порожніх рядків у функціях."""

from pathlib import Path

import pytest
from check_function_blank_lines import find_violations, main

CLEAN_WITH_DOCSTRING = '''
def sample() -> int:
    """Опис.

    Returns
    -------
    int
        Значення.
    """
    value = 1
    return value
'''

CLEAN_WITH_MULTILINE_STRING = '''
def sample() -> str:
    text = """перший

    другий"""
    return text
'''

CLEAN_WITH_MULTILINE_FSTRING = '''
def sample(name: str) -> str:
    text = f"""привіт

    {name}"""
    return text
'''

CLEAN_MODULE_AND_CLASS_SPACING = """
import os


class Sample:
    value = 1

    def first(self) -> int:
        return 1

    def second(self) -> int:
        return 2


def top() -> int:
    return os.getpid()
"""

BLANK_BETWEEN_STATEMENTS = """
def sample() -> int:
    first = 1

    return first
"""

BLANK_AFTER_DOCSTRING = '''
def sample() -> int:
    """Опис."""

    return 1
'''

BLANK_INSIDE_BLOCK = """
def sample(flag: bool) -> int:
    if flag:
        value = 1

        return value
    return 0
"""

BLANK_IN_ASYNC = """
async def sample() -> int:
    first = 1

    return first
"""


@pytest.mark.parametrize(
    "source",
    [
        CLEAN_WITH_DOCSTRING,
        CLEAN_WITH_MULTILINE_STRING,
        CLEAN_WITH_MULTILINE_FSTRING,
        CLEAN_MODULE_AND_CLASS_SPACING,
    ],
)
def test_allowed_cases_have_no_violations(source: str) -> None:
    """Дозволені випадки не дають порушень."""
    assert find_violations(source) == []


@pytest.mark.parametrize(
    ("source", "line"),
    [
        (BLANK_BETWEEN_STATEMENTS, 4),
        (BLANK_AFTER_DOCSTRING, 4),
        (BLANK_INSIDE_BLOCK, 5),
        (BLANK_IN_ASYNC, 4),
    ],
)
def test_forbidden_cases_are_reported(source: str, line: int) -> None:
    """Заборонені випадки повертають номер рядка."""
    assert find_violations(source) == [line]


def test_main_reports_and_returns_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Main повертає 1 і друкує місце порушення."""
    path = tmp_path / "bad.py"
    path.write_text(BLANK_BETWEEN_STATEMENTS, encoding="utf-8")
    assert main([str(path)]) == 1
    assert f"{path}:4:" in capsys.readouterr().out


def test_main_accepts_clean_file(tmp_path: Path) -> None:
    """Main повертає 0 для чистого файлу."""
    path = tmp_path / "good.py"
    path.write_text(CLEAN_WITH_DOCSTRING, encoding="utf-8")
    assert main([str(path)]) == 0


def test_main_reports_syntax_error(tmp_path: Path) -> None:
    """Синтаксична помилка дає код 1."""
    path = tmp_path / "broken.py"
    path.write_text("def (:\n", encoding="utf-8")
    assert main([str(path)]) == 1

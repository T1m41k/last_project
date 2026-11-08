"""Pre-commit hook: заборона порожніх рядків між інструкціями у тілі функцій."""

import ast
import io
import sys
import tokenize
from collections.abc import Sequence
from pathlib import Path


def _string_literal_lines(source: str) -> set[int]:
    """Зібрати номери рядків, що належать рядковим літералам.

    Parameters
    ----------
    source : str
        Вихідний код модуля.

    Returns
    -------
    set[int]
        Номери рядків усередині рядкових літералів (включно з f-рядками).
    """
    protected: set[int] = set()
    fstring_starts: list[int] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.FSTRING_START:
            fstring_starts.append(token.start[0])
        elif token.type == tokenize.FSTRING_END:
            protected.update(range(fstring_starts.pop(), token.end[0] + 1))
        elif token.type == tokenize.STRING:
            protected.update(range(token.start[0], token.end[0] + 1))
    return protected


def find_violations(source: str) -> list[int]:
    """Знайти порожні рядки між інструкціями у тілах функцій.

    Порожні рядки всередині docstring та багаторядкових рядкових літералів
    дозволені. Порожній рядок одразу після docstring заборонений.

    Parameters
    ----------
    source : str
        Вихідний код модуля.

    Returns
    -------
    list[int]
        Відсортовані номери рядків-порушень (нумерація з 1).

    Raises
    ------
    SyntaxError
        Якщо код неможливо розібрати.
    """
    tree = ast.parse(source)
    lines = source.splitlines()
    protected = _string_literal_lines(source)
    violations: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            first = node.body[0].lineno
            last = node.end_lineno or first
            for number in range(first, last + 1):
                if not lines[number - 1].strip() and number not in protected:
                    violations.add(number)
    return sorted(violations)


def main(argv: Sequence[str] | None = None) -> int:
    """Перевірити файли, передані аргументами командного рядка.

    Parameters
    ----------
    argv : Sequence[str] | None
        Шляхи до файлів; за замовчуванням береться sys.argv.

    Returns
    -------
    int
        0, якщо порушень немає, інакше 1.
    """
    paths = sys.argv[1:] if argv is None else list(argv)
    exit_code = 0
    for path in paths:
        try:
            violations = find_violations(Path(path).read_text(encoding="utf-8"))
        except SyntaxError as error:
            print(f"{path}: синтаксична помилка: {error}")
            exit_code = 1
            continue
        for number in violations:
            print(f"{path}:{number}: порожній рядок у тілі функції")
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

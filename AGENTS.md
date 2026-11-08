# AGENTS.md — інструкції для AI-агента

Проєкт: Telegram-бот «Облік книг» + FastAPI (/health, /api/v1/admin/stats). Мова коментарів, docstring і повідомлень бота — українська.

## Структура

- `app/api` — HTTP-маршрути й залежності FastAPI (без SQL і бізнес-правил).
- `app/bot` — обробники бота (`handlers.py`, без SQL і без імпортів aiogram) та адаптер Telegram (`telegram_adapter.py`).
- `app/services` — бізнес-правила; викликають лише repositories.
- `app/repositories` — єдине місце з SQL/SQLAlchemy-запитами.
- `app/models`, `app/schemas`, `app/core` — ORM, Pydantic, конфігурація/БД/безпека.
- `app/_detail` — `constants.py` (усі ліміти й повторювані значення) та тематичні `helpers.py` у підпакетах. Не створювати універсальний «utils».
- `tests/unit`, `tests/integration`, `alembic/`, `scripts/`.

## Стиль

- Python 3.12, повна типізація (`mypy --strict` для `app/`), NumPy-style docstring для модулів, класів і функцій.
- Ruff: E4, E7, E9, F, I, UP, B, SIM, N, C4, D, S (D = numpy). `S101` дозволено лише в `tests/`.
- У тілі функції **немає порожніх рядків між інструкціями** (їх перевіряє `scripts/check_function_blank_lines.py`). Тому без вкладених функцій/замикань — виносити на рівень модуля.
- Нікнейм ніколи не є ідентифікатором: лише `platform_user_id`. Права адміністратора — лише з `ADMIN_PLATFORM_IDS`/`ADMIN_API_TOKEN`.

## Заборони

- Не додавати SQL у `handlers`/`api`. Не дублювати бізнес-правила.
- Не вимикати перевірки глобально, не робити `exclude` для `app/`, не ставити масові `noqa`/`type: ignore`.
- Не коммітити `.env`, токени й секрети. Не використовувати реальний токен Telegram у тестах.
- Не змінювати схему БД без міграції Alembic.

## Команди перевірки

```bash
pre-commit install
pre-commit run --all-files
alembic upgrade head
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/bookbot_test pytest --cov --cov-fail-under=80
docker build -t book-bot .
```

## Порядок роботи агента

1. Прочитати ТЗ (`docs/` і README). 2. Скласти план. 3. Виконати обмежену зміну. 4. Додати/оновити тести. 5. Запустити перевірки. 6. Переглянути diff. 7. Записати взаємодію в `docs/ai-log.md`.

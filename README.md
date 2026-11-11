# Book Tracker Bot — Telegram-бот «Облік книг»

Фінальний проєкт (Python Backend, ТЗ 02 «Telegram або Discord Bot»). Бот на платформі **Telegram** веде облік книг користувача, а FastAPI надає перевірку готовності та адміністративну статистику.

## Сценарії (зафіксовано до реалізації)

1. `/start` — реєстрація за `platform_user_id`, пояснення призначення й команд.
2. `/add` — діалог: назва → автор → сторінки → підсумок → підтвердження «так/ні» → запис до БД. `/cancel` скасовує діалог на будь-якому кроці.
3. `/list [сторінка]`, `/book <id>`, `/update <id> <поле> <значення>`, `/delete <id>` — перегляд, зміна й видалення **лише власних** записів.
4. `/stats` — кількість користувачів і записів лише для `ADMIN_PLATFORM_IDS`.
5. Повторно отримана подія (той самий `update_id`) не створює дублікат.
6. Незавершений діалог переживає перезапуск, бо стан лежить у PostgreSQL.

## Реалізовані функції

- 9 команд: `/start`, `/help`, `/add`, `/list`, `/book`, `/update`, `/delete`, `/cancel`, `/stats` (п'ять змістовних команд — `/add`, `/list`, `/book`, `/update`, `/delete`).
- Валідація: назва ≤ 200, автор ≤ 120, нотатка ≤ 1000 символів, сторінки — ціле 1–10000, статус — `planned|reading|finished` (або «заплановано/читаю/прочитано»). Невідома команда й відсутній запис дають зрозумілу відповідь.
- Ізоляція користувачів: усі запити фільтруються за власником; чужий запис поводиться як відсутній.
- Ідемпотентність: таблиця `processed_events` з унікальністю `(platform, platform_event_id)`; ідентифікатор події фіксується в тій самій транзакції, що й зміни даних.
- Помилка або тайм-аут Telegram під час відповіді логуються і не скасовують уже збережені дані.
- FastAPI: `GET /health` (200/503), `GET /api/v1/admin/stats` (Bearer `ADMIN_API_TOKEN`), документація `/docs`.

## Стек

Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async) + asyncpg, Alembic, PostgreSQL (Neon), aiogram 3 (long polling), pytest, Ruff, mypy, pre-commit, Docker.

## Структура

```
app/
  main.py              # FastAPI + запуск бота у lifespan
  api/                 # маршрути й залежності (health, admin)
  bot/                 # handlers (без SQL), контракти, тексти, адаптер aiogram
  schemas/             # Pydantic
  models/              # SQLAlchemy: BotUser, Book, DialogState, ProcessedEvent
  services/            # бізнес-правила (спільні для бота і API)
  repositories/        # усі запити до БД
  core/                # config, database, security, exceptions
  _detail/             # constants.py + тематичні helpers.py
tests/unit, tests/integration
alembic/               # міграції
scripts/               # custom pre-commit hook
.github/workflows/ci.yml
docs/                  # ai-log.md, опис PR
```

## Налаштування `.env`

```bash
cp .env.example .env
```

| Змінна | Призначення |
| --- | --- |
| `DATABASE_URL` | рядок Neon (`postgresql://...?sslmode=require`); TLS зберігається, URL автоматично перетворюється для asyncpg |
| `BOT_TOKEN` | токен від @BotFather |
| `ADMIN_PLATFORM_IDS` | Telegram user id адміністраторів через кому |
| `ADMIN_API_TOKEN` | токен для `/api/v1/admin/stats` |
| `BOT_POLLING_ENABLED` | `false` — не запускати polling |

JWT/email-реєстрація тут не використовується: за ТЗ її замінює ідентифікація за `platform_user_id`.

## Запуск у Docker

```bash
docker compose up --build
```

Контейнер на старті виконує `alembic upgrade head`, потім запускає uvicorn. Окремо міграції: `docker compose run --rm app alembic upgrade head`.

Без Docker: `pip install -r requirements-dev.txt && alembic upgrade head && uvicorn app.main:app`.

## Тести та hooks

Для інтеграційних тестів потрібен PostgreSQL (не Neon-прод!). Локально:

```bash
docker compose --profile test up -d postgres-test
export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/bookbot_test
export DATABASE_URL=$TEST_DATABASE_URL ADMIN_API_TOKEN=local-key BOT_POLLING_ENABLED=false
alembic upgrade head
pytest --cov --cov-fail-under=80
pre-commit install
pre-commit run --all-files
```

Без `TEST_DATABASE_URL` інтеграційні тести пропускаються. Виклики Telegram у тестах замінені підробками; токен не потрібен. Тести покривають команди, стан діалогу, ізоляцію користувачів, повтор події, відмову неадміністратору, помилку/тайм-аут платформи, `/health`, `/stats` та сам hook.

Власний hook `scripts/check_function_blank_lines.py` забороняє порожні рядки між інструкціями в тілах функцій (дозволені всередині docstring і багаторядкових рядків).

## API

Swagger: <http://localhost:8000/docs>. Статуси `/api/v1/admin/stats`: 200; 401 — немає Bearer-заголовка; 403 — токен неправильний.

## Приклад відтворюваного сценарію

1. `docker compose up --build`, у Telegram відкрийте бота.
2. `/start` → `/add` → `Дюна` → `Френк Герберт` → `600` → `так` (бот: «Збережено! #1 · Дюна — Френк Герберт (600 с.) · заплановано»).
3. `/list`, `/book 1`, `/update 1 status finished`, `/delete 1`, `/book 1` → «Запис #1 не знайдено.»
4. `/add`, `Назва`, зупиніть контейнер (`docker compose stop`), запустіть знову, надішліть автора — діалог продовжиться; `/cancel` його скасує.
5. `curl -H "Authorization: Bearer $ADMIN_API_TOKEN" localhost:8000/api/v1/admin/stats` → `{"users_count":1,"books_count":0}`.

## Відомі обмеження

- Лише приватні чати Telegram; Discord не реалізовано.
- Long polling: у режимі кількох реплік дві копії конкурували б за оновлення — запускайте одну.
- Один тип діалогу (`/add`); оновлення виконується однорядковою командою.
- Подія фіксується в БД до відправки відповіді: якщо Telegram недоступний, запис збережеться, але відповідь не буде повторена.
- Нотатка зберігається в один рядок (внутрішні пробіли й переноси нормалізуються).

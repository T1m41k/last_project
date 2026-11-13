# Архітектура проєкту «Book Tracker Bot»

## 1. Призначення та загальний опис

Проєкт Telegram-бот для обліку книг. Користувач через команди створює, переглядає, змінює й видаляє власні записи про книги. Поруч працює FastAPI-застосунок з двома ендпоїнтами: перевірка готовності (`GET /health`) і адміністративна статистика (`GET /api/v1/admin/stats`).

Бот і FastAPI живуть в одному процесі: long polling Telegram запускається у фоновій задачі в `lifespan` FastAPI. Обидва шари використовують **спільні сервіси та репозиторії**, тому бізнес-правила не дублюються.

Основні сутності: `BotUser` (користувач), `Book` (предметна сутність), `DialogState` (стан багатокрокового діалогу), `ProcessedEvent` (службова таблиця для ідемпотентності).

## 2. Архітектура


Правила залежностей, які дотримано в коді:

- `api` і `bot/handlers` **не містять SQL**; вони викликають `services`.
- `services` викликають лише `repositories`; бізнес-правила (валідація, права власника, кроки діалогу) живуть тільки тут.
- `repositories` — єдине місце з запитами SQLAlchemy.
- `bot/handlers.py` **не імпортує aiogram**. Він залежить від протоколу `MessageSender` і датакласу `IncomingMessage` (`bot/contracts.py`). Завдяки цьому в тестах Telegram замінюється підробкою, а бібліотеку платформи можна змінити, не чіпаючи логіку.
- `app/_detail` містить внутрішні `constants.py` та тематичні `helpers.py` (валідація, розбір повідомлень, форматування).

### 2.1. Життєвий цикл застосунку

`app/main.py` у `lifespan`: читає налаштування → створює асинхронний рушій і фабрику сесій → кладе їх у `app.state` → якщо `BOT_POLLING_ENABLED=true`, створює `BotRuntime` і запускає polling → на завершенні зупиняє бота та закриває пул з'єднань.

### 2.2. Обробка одного повідомлення

1. aiogram отримує оновлення, `on_message` перетворює його на `IncomingMessage` (`update_id` стає `event_id`, `from_user.id` — `platform_user_id`).
2. `BotHandlers.handle_message` відкриває **одну транзакцію** (`session.begin()`).
3. `EventService.claim` намагається вставити `(platform, event_id)` в `processed_events` (`INSERT ... ON CONFLICT DO NOTHING`). Якщо запис уже є — це повторна подія, обробка завершується без відповіді.
4. `UserService.register` знаходить або атомарно створює користувача за `platform_user_id` (нікнейм не використовується).
5. Текст розбирається: команда (`/name@bot args`) або звичайний текст. Якщо є активний діалог, звичайний текст є відповіддю на його крок, а більшість команд (крім `/start`, `/help`, `/cancel`) заміщуються нагадуванням завершити діалог.
6. Команда виконується через сервіси; доменні помилки (`AppError`) перетворюються на зрозумілу відповідь.
7. Транзакція фіксується, **після цього** відповідь надсилається. Помилка чи тайм-аут платформи (`PlatformError`, `TimeoutError`) логується й не скасовує збережені дані. Неочікувана помилка дає загальну відповідь без внутрішніх деталей, транзакція відкочується (подію можна обробити повторно).

### 2.3.1. Діалог `/add`

Кроки: `title → author → pages → confirm`. Після кожного кроку стан (`flow`, `step`, `data` у JSONB) зберігається в `dialog_states` — по одному запису на користувача. На кроці `confirm` показується підсумок; «так» створює книгу й видаляє стан, «ні» або `/cancel` лише видаляє стан. Невалідне введення не змінює крок і повертає причину помилки. Оскільки стан лежить у БД, діалог переживає перезапуск застосунку.

### 2.4. Безпека та ізоляція

- Ідентифікатор користувача — лише `platform_user_id` (незмінний числовий id Telegram).
- Усі вибірки книг обмежені `owner_id`; чужий запис поводиться як відсутній («не знайдено»), без розкриття його існування.
- Адміністратор бота визначається серверним `ADMIN_PLATFORM_IDS`, а не повідомленням. REST-статистика захищена `ADMIN_API_TOKEN` (Bearer, порівняння через `secrets.compare_digest`): немає заголовка — 401, неправильний токен — 403.
- Секрети беруться зі змінних середовища; `.env` не потрапляє в Git та образ.

## 3. Модель даних

| Таблиця | Призначення | Ключові обмеження |
| --- | --- | --- |
| `bot_users` | користувачі | `UNIQUE(platform_user_id)`, `platform_user_id BIGINT` |
| `books` | книги користувачів | FK `owner_id → bot_users.id ON DELETE CASCADE`, індекс `(owner_id, id)` |
| `dialog_states` | стан діалогу | `UNIQUE(user_id)`, FK з `ON DELETE CASCADE`, `data JSONB` |
| `processed_events` | оброблені події платформи | `UNIQUE(platform, platform_event_id)` |

Схема створюється міграцією Alembic `alembic/versions/initial_schema.py`. Підключення до Neon: `sslmode=require` з `DATABASE_URL` перетворюється на `ssl=require` для asyncpg (`core/database.py::to_async_url`).

## 4. Структура та організація коду

```
app/
  main.py                    # create_app(), lifespan: БД + запуск бота
  api/
    dependencies.py          # get_session, get_app_settings, require_admin
    health.py                # GET /health
    admin.py                 # GET /api/v1/admin/stats
  bot/
    contracts.py             # IncomingMessage, протокол MessageSender
    handlers.py              # BotHandlers: дедуплікація, реєстрація, команди, діалоги
    texts.py                 # тексти відповідей і запити кроків діалогу
    telegram_adapter.py      # AiogramSender, on_message, BotRuntime, create_bot_runtime
  schemas/                   # Pydantic: HealthResponse, AdminStatsResponse
  models/                    # Base, BotUser, Book, DialogState, ProcessedEvent
  services/
    container.py             # build_services(session) -> Services
    user_service.py, book_service.py, dialog_service.py,
    add_book_dialog_service.py, event_service.py,
    stats_service.py, health_service.py
  repositories/              # user, book, dialog, event, health
  core/                      # config.py, database.py, security.py, exceptions.py
  _detail/
    constants.py             # усі ліміти, коди команд, статуси, кроки діалогу
    validation/helpers.py    # normalize_text, parse_pages, parse_status, ...
    bot/helpers.py           # parse_command, is_yes/is_no, truncate_message
    formatting/helpers.py    # format_book_line/details/list, format_summary
tests/
  unit/, integration/, conftest.py, support.py
alembic/                     # env.py (async), versions/initial_schema.py
scripts/                     # check_function_blank_lines.py (custom hook)
.github/workflows/ci.yml
Dockerfile, compose.yaml, .env.example, .pre-commit-config.yaml, pyproject.toml
```

Принципи організації:

- **Один модуль — одна відповідальність**; бізнес-ліміти й повторювані значення лише в `constants.py`; допоміжні функції згруповано за темою, без універсального «utils».
- **Типізація і документація**: повні анотації (`mypy --strict` для `app/`), NumPy-style docstring, у тілах функцій немає порожніх рядків між інструкціями (перевіряє власний hook), тому вкладених функцій немає.
- **Фабрика сервісів** `build_services(session)` збирає всі сервіси над однією сесією; її використовують і бот, і FastAPI.
- **Асинхронність наскрізна**: SQLAlchemy async + asyncpg, aiogram, FastAPI.

## 5. Стратегія тестування

### 5.1. Рівні та інфраструктура

- **Модульні тести** (`tests/unit`) не потребують БД: чисті функції, сервіси на репозиторіях у пам'яті (`FakeBookRepository`, `FakeDialogRepository`), адаптер Telegram із `AsyncMock`, власний hook.
- **Інтеграційні тести** (`tests/integration`) працюють із реальним PostgreSQL (`TEST_DATABASE_URL`, у CI — сервіс `postgres:16`). Перед кожним тестом таблиці очищаються (`TRUNCATE ... RESTART IDENTITY`). Бот перевіряється наскрізно: `Chat.say("/add")` → `BotHandlers` → сервіси → БД → `FakeSender`.
- Виклики Telegram скрізь замінені підробками (`FakeSender`, mock `Bot`); реальний токен не потрібен. API тестується через `httpx.AsyncClient` з `ASGITransport`.
- У CI: `pre-commit run --all-files` → `alembic upgrade head` на чистій БД → `pytest --cov --cov-fail-under=80` → `docker build`.

### 5.2. Що перевіряють тести

**Модульні**

| Файл | Що перевіряє |
| --- | --- |
| `test_validation_helpers.py` | нормалізація тексту, ліміти довжини, кількість сторінок (1–10000, нецифри, `²`, від'ємні), додатні цілі, статуси та їхні українські аліаси, назви полів, очищення нотатки символом «-» |
| `test_bot_helpers.py` | розбір команд (`/Book@bot 5`, порожній `/`, не-команда), відповіді так/ні, обрізання довгого повідомлення, форматування книги, списку (підказка наступної сторінки) та підсумку діалогу |
| `test_config_and_security.py` | розбір `ADMIN_PLATFORM_IDS` зі змінної середовища, порожнє значення за замовчуванням, `get_settings`, перетворення Neon-URL (`sslmode`→`ssl`, відкидання `channel_binding`), порівняння токена |
| `test_services.py` | створення з валідацією, приховування чужих книг, оновлення кожного поля й видалення, стабільна пагінація; діалог: успішний шлях, помилка валідації зберігає крок, «ні» та незрозуміла відповідь, пошкоджений крок |
| `test_telegram_adapter.py` | успішна відправка, перетворення `TelegramAPIError` і тайм-ауту на `PlatformError`, конвертація `Update` у `IncomingMessage`, ігнорування повідомлень без відправника, вимога `BOT_TOKEN`, запуск і зупинка polling |
| `test_check_function_blank_lines.py` | custom hook: дозволені випадки (docstring, багаторядкові й f-рядки, відступи між методами) і заборонені (між інструкціями, після docstring, у вкладеному блоці, у `async`), `main` з кодами 0/1 і синтаксичною помилкою |

**Інтеграційні (PostgreSQL)**

| Файл | Що перевіряє |
| --- | --- |
| `test_bot_commands.py` | `/start` реєструє користувача за `platform_user_id` один раз; `/help`, невідома команда, текст поза діалогом; **повний CRUD** (`/add`→`/list`→`/book`→`/update`→`/delete`); валідація кроків діалогу; скасування (`ні`, `/cancel`); блокування команд під час діалогу; **відновлення діалогу після «перезапуску»** (нові `BotHandlers` над тією самою БД); **ізоляція користувачів** (читання, зміна, видалення, діалоги); перевірка аргументів команд; пагінація `/list`; **повтор події не дублює запис**; `/stats` лише для адміністраторів; **помилка й тайм-аут платформи не втрачають дані**; неочікувана помилка не розкриває деталей |
| `test_api.py` | `/health` 200 і 503 (недоступна БД); `/api/v1/admin/stats`: 401 без заголовка та зі схемою не Bearer, 403 за неправильного токена, 200 з коректними лічильниками; доступність `/docs` і `openapi.json` |
| `test_app_lifecycle.py` | `lifespan` без бота готує `app.state`; з увімкненим polling бот запускається й зупиняється разом із застосунком |

## 6. Якість коду та автоматизація

- **pre-commit**: Ruff lint (E4, E7, E9, F, I, UP, B, SIM, N, C4, D за numpy, S) і Ruff format, `mypy --strict` для `app/`, Gitleaks, `detect-private-key`, `check-yaml`, `check-toml`, `check-merge-conflict`, `check-added-large-files`, `end-of-file-fixer`, `trailing-whitespace`, власний hook порожніх рядків.
- **CI** (`.github/workflows/ci.yml`) запускається на `push` і `pull_request` і перевіряє все перелічене вище, поріг покриття та збірку Docker-образу.
- **Docker**: образ запускає `alembic upgrade head`, потім uvicorn; `compose.yaml` має профіль `test` з локальним PostgreSQL для тестів.
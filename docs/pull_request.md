# PR: Telegram-бот «Облік книг» + FastAPI

## Мета
Завершений backend за ТЗ 02: Telegram-бот обліку книг, спільні сервіси/репозиторії для бота й FastAPI.

## Реалізовані функції
`/start`, `/help`, `/add` (діалог із підтвердженням і станом у PostgreSQL), `/list`, `/book`, `/update`, `/delete`, `/cancel`, `/stats` (адмін); `GET /health`; `GET /api/v1/admin/stats` (Bearer).

## Архітектурні рішення та БД
- aiogram 3, long polling у lifespan FastAPI; handlers не залежать від aiogram і не містять SQL (відправник — протокол, у тестах mock).
- Таблиці: `bot_users` (унікальний `platform_user_id`), `books`, `dialog_states` (один на користувача, JSONB), `processed_events` (унікальність `(platform, platform_event_id)` для ідемпотентності).
- Подія фіксується в одній транзакції зі змінами даних; відповідь надсилається після коміту.
- Neon: `sslmode=require` перетворюється на `ssl=require` для asyncpg.

## Перевірка з чистого clone
```bash
git clone <repo> && cd <repo> && git checkout final/book-tracker-bot
cp .env.example .env   # заповнити
docker compose up --build
pip install -r requirements-dev.txt && pre-commit run --all-files
docker compose --profile test up -d postgres-test   # + змінні з README
pytest --cov --cov-fail-under=80
```

## Результати тестів/CI
_Вставити після першого зеленого запуску CI._

## Відомі обмеження
Див. розділ у README.

## Використання AI
Так. Код згенеровано Claude (claude.ai) за запитом студента; AGENTS.md створено до першої взаємодії; деталі та власні висновки — у `docs/ai-log.md`.

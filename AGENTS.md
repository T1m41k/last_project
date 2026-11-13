# AGENTS.md — інструкції для AI-агента

Проєкт: Telegram-бот «Облік книг» + FastAPI (`GET /health`, `GET /api/v1/admin/stats`). Python 3.12, async SQLAlchemy + asyncpg, PostgreSQL (Neon), aiogram 3 (long polling), Alembic.
Мова коментарів, docstring, повідомлень бота, README і документації — **українська**. Ідентифікатори в коді — англійською.

Перед будь-якою зміною прочитай: `README.md`, `docs/architecture.md`, цей файл. Якщо завдання суперечить їм — зупинись і запитай людину.

## 1. Команди

```bash
pip install -r requirements-dev.txt                   # залежності (Python 3.12!)
pre-commit install                                    # один раз
pre-commit run --all-files                            # ruff, ruff format, mypy --strict, gitleaks, custom hook
alembic upgrade head                                  # міграції (потрібні DATABASE_URL та ADMIN_API_TOKEN)
pytest --cov --cov-fail-under=80                      # тести (інтеграційним потрібен TEST_DATABASE_URL)
docker build -t book-bot .                            # перевірка образу
docker compose up --build                             # запуск (потрібен .env)
docker compose --profile test up -d postgres-test     # локальний PostgreSQL для тестів, порт 5433
```

Локальні змінні для тестів: `TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/bookbot_test`, `DATABASE_URL` — те саме значення, `ADMIN_API_TOKEN` — будь-який рядок, `BOT_POLLING_ENABLED=false`.

## 2. Структура і відповідальність

| Каталог | Що тут | Чого тут бути не може |
| --- | --- | --- |
| `app/api` | маршрути FastAPI, залежності (`get_session`, `require_admin`) | SQL, бізнес-правила |
| `app/bot/handlers.py` | маршрутизація команд і діалогів | SQL, імпорти `aiogram` |
| `app/bot/telegram_adapter.py` | єдине місце з aiogram (`AiogramSender`, `on_message`, `BotRuntime`) | бізнес-логіка |
| `app/services` | бізнес-правила, валідація, права власника | прямі запити до БД |
| `app/repositories` | усі запити SQLAlchemy | бізнес-правила |
| `app/models`, `app/schemas` | ORM-моделі, Pydantic-схеми | логіка |
| `app/core` | `config`, `database`, `security`, `exceptions` | предметна логіка |
| `app/_detail` | `constants.py` + тематичні `helpers.py` у підпакетах (`validation`, `bot`, `formatting`) | універсальний «utils» |
| `tests/unit`, `tests/integration` | тести; фікстури в `conftest.py`, підробки в `support.py` | — |

Напрямок викликів: `api`/`bot` → `services` → `repositories` → БД. Зворотних залежностей немає. Нові сервіси реєструй у `services/container.py` (`Services`, `build_services`).

## 3. Стиль коду (перевіряється автоматично)

- Повні типи; `mypy --strict` для `app/`. Без `Any`, окрім JSONB-даних і `app.state`.
- NumPy-style docstring для кожного модуля, класу й публічної функції (`Parameters`, `Returns`, `Raises` — за змістом). `__init__` без docstring. Перший рядок закінчується крапкою. У тестах — одно­рядкові docstring.
- Ruff: `E4, E7, E9, F, I, UP, B, SIM, N, C4, D (numpy), S`. `S101` дозволено лише в `tests/`. Інші винятки — лише точкові з поясненням. Заборонено: глобальне вимкнення правил, `exclude` для `app/`, масові `noqa` / `type: ignore`.
- **У тілі функції немає порожніх рядків між інструкціями** (виняток: усередині docstring і багаторядкових рядків). Наслідок: **жодних вкладених функцій і замикань** — `ruff format` вставляє перед ними порожній рядок. Виноси такий код на рівень модуля.
- Повторювані значення й бізнес-ліміти — лише в `app/_detail/constants.py`. Не хардкодь числа й рядки команд у логіці.
- FastAPI: залежності через `Annotated[..., Depends(...)]` (інакше спрацює `B008`); параметри запиту — `Annotated[int, Query(...)]`.
- Не називай змінні зі строковим літералом словами `password`, `token`, `secret` (спрацює `S105/S106`). У тестах секрети — константи на кшталт `ADMIN_KEY`, що передаються як змінні, а не літерали в аргументах.
- Тексти для користувача бота — у `app/bot/texts.py`; форматування — у `app/_detail/formatting/helpers.py`.

## 4. Правила предметної області

- Користувач ідентифікується **лише** `platform_user_id`; нікнейм — не ідентифікатор.
- Користувач бачить і змінює **лише свої** записи: усі вибірки книг фільтруються за `owner_id`; чужий запис поводиться як відсутній.
- Адміністратор бота — лише за `ADMIN_PLATFORM_IDS` (серверна конфігурація). REST-статистика — лише `ADMIN_API_TOKEN` у `Authorization: Bearer`: немає заголовка → 401, неправильний токен → 403.
- Кожна подія платформи реєструється в `processed_events` (унікальність `(platform, platform_event_id)`) **у тій самій транзакції**, що й зміни даних. Повтор не дублює запис.
- Стан діалогу зберігається в `dialog_states` (PostgreSQL), один на користувача; `/cancel` його видаляє.
- Відповідь користувачу надсилається **після** коміту; помилка або тайм-аут платформи не скасовує збережені дані.
- Користувач ніколи не бачить трасувань і внутрішніх помилок.

## 5. База даних і міграції

- Будь-яка зміна моделей = нова міграція в `alembic/versions/` (файл `<slug>.py`, ім'я **не** починається з цифри — інакше `N999`). Міграція має працювати на чистій БД: перевір `alembic upgrade head`, потім `alembic downgrade -1` і знову `upgrade head`.
- Атомарність — через `INSERT ... ON CONFLICT`, а не «спочатку перевір, потім вставляй».
- Neon: `sslmode=require` перетворюється на `ssl=require` для asyncpg у `core/database.py::to_async_url`. Не прибирай TLS-параметри.

## 6. Тести

- Кожна нова поведінка має тест; кожен виправлений баг — регресійний тест.
- Сервіси й помічники — модульні тести (репозиторії в пам'яті з `tests/support.py`). Команди бота й API — інтеграційні тести на реальному PostgreSQL (`Chat.say("/команда")`, `api_client`).
- Telegram у тестах — лише підробки (`FakeSender`, `AsyncMock`). **Не використовуй реальний токен і мережу.**
- Обов'язково покрити: успіх, валідацію, відсутній запис, ізоляцію користувачів, повтор події, відмову неадміністратору, помилку/тайм-аут платформи.
- Тести асинхронні (`asyncio_mode = "auto"`), підключення в тестах — `NullPool`.
- Поріг покриття — 80 %; не знижуй його, щоб «пройти» CI.

## 7. Git

- Робоча гілка `final/book-tracker-bot` від `main`; результат — один PR у `main`.
- Малі завершені коміти в стилі Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `build:`, `chore:`). Не робити один підсумковий коміт і не дробити штучно. Не переписувати опубліковану історію (`push --force` заборонено).
- Не коміть `.env`, токени, ключі, дампи БД. `.env.example` містить лише безпечні приклади.

## 8. Порядок роботи

1. Прочитати ТЗ, `README.md`, `docs/architecture.md`. 2. Скласти короткий план (які файли, які тести). 3. Виконати **одну обмежену зміну**. 4. Додати або оновити тести. 5. Запустити `pre-commit run --all-files` і `pytest`. 6. Переглянути `git diff` — прибрати зайве, перевірити, що не порушено шарів і правил розділів 3–5. 7. Закомітити. 8. Дописати запис у `docs/ai-log.md`.

## 9. Журнал AI (`docs/ai-log.md`)

Після кожної взаємодії додай запис: **запит**, **дії агента**, **змінені файли або коміт**, **виконані перевірки** (які саме й з яким результатом; чесно вказуй, що не запускалось), **висновок студента** (залишай поле для людини, не вигадуй його за неї).

## 10. Чекліст «готово»

- [ ] `pre-commit run --all-files` — без помилок і без змін у файлах
- [ ] `pytest --cov --cov-fail-under=80` — зелений
- [ ] `alembic upgrade head` працює на чистій БД; для змін моделей є міграція
- [ ] `docker build -t book-bot .` проходить
- [ ] немає SQL у `api`/`bot/handlers`, немає імпортів aiogram поза `telegram_adapter.py`
- [ ] немає секретів у коді, `.env.example` оновлено за потреби
- [ ] README і `docs/architecture.md` відповідають коду
- [ ] запис у `docs/ai-log.md` додано

## 11. Відомі пастки

- Потрібен **Python 3.12**: для 3.13+ немає готових збірок деяких закріплених залежностей.
- `aiogram 3.15` вимагає `pydantic<2.10`; не підвищуй `pydantic` без оновлення aiogram (у `requirements.txt` і `additional_dependencies` mypy у `.pre-commit-config.yaml` версії мають збігатися).
- `Settings()` викликається без аргументів лише через `get_settings()`; поля без значень за замовчуванням (`database_url`, `admin_api_token`) мають бути в середовищі.
- На Windows оточення активується `.venv\Scripts\Activate.ps1`; за заборони скриптів — `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- Репозиторій краще тримати поза OneDrive: він псує `.git` і `.venv`.

## 12. Коли зупинитись і запитати людину

Невизначеність у вимогах ТЗ; потреба змінити схему БД поза міграцією; потреба вимкнути перевірку чи знизити поріг покриття; потреба додати залежність; будь-які дії з реальними секретами, Neon-продом чи Telegram.

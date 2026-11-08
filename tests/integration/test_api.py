"""Інтеграційні тести FastAPI (потребують PostgreSQL)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.health_repository import HealthRepository
from app.services.container import build_services
from tests.conftest import ADMIN_KEY, USER_ID
from tests.support import Chat

STATS_URL = "/api/v1/admin/stats"


def bearer(value: str) -> dict[str, str]:
    """Сформувати заголовок Authorization."""
    return {"Authorization": f"Bearer {value}"}


async def failing_ping(_: HealthRepository) -> None:
    """Імітувати недоступну базу даних."""
    raise SQLAlchemyError("база недоступна")


async def test_health_ok(api_client: AsyncClient) -> None:
    """GET /health повертає 200, коли БД відповідає."""
    response = await api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


async def test_health_unavailable(api_client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /health повертає 503, коли БД недоступна."""
    monkeypatch.setattr(HealthRepository, "ping", failing_ping)
    response = await api_client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "error"}


async def test_stats_requires_authentication(api_client: AsyncClient) -> None:
    """Без заголовка Authorization — 401."""
    response = await api_client.get(STATS_URL)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_stats_rejects_other_scheme(api_client: AsyncClient) -> None:
    """Схема, відмінна від Bearer, вважається відсутньою автентифікацією."""
    response = await api_client.get(STATS_URL, headers={"Authorization": "Basic abc"})
    assert response.status_code == 401


async def test_stats_rejects_wrong_token(api_client: AsyncClient) -> None:
    """Неправильний токен — 403."""
    response = await api_client.get(STATS_URL, headers=bearer("неправильний"))
    assert response.status_code == 403
    assert "ADMIN" not in response.text


async def test_stats_returns_counts(
    api_client: AsyncClient, chat: Chat, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Правильний токен повертає кількість користувачів і записів."""
    empty = await api_client.get(STATS_URL, headers=bearer(ADMIN_KEY))
    assert empty.json() == {"users_count": 0, "books_count": 0}
    await chat.say("/start")
    async with session_factory() as session, session.begin():
        services = build_services(session)
        user, _ = await services.users.register(USER_ID, None)
        await services.books.create(user.id, title="Дюна", author="Герберт", pages=600)
    response = await api_client.get(STATS_URL, headers=bearer(ADMIN_KEY))
    assert response.status_code == 200
    assert response.json() == {"users_count": 1, "books_count": 1}


async def test_docs_and_openapi_are_available(api_client: AsyncClient) -> None:
    """Документація /docs і схема OpenAPI доступні."""
    assert (await api_client.get("/docs")).status_code == 200
    paths = (await api_client.get("/openapi.json")).json()["paths"]
    assert STATS_URL in paths and "/health" in paths

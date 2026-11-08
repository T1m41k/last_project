"""Залежності FastAPI: сесія БД, налаштування, перевірка адміністратора."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.security import is_valid_admin_token

bearer_scheme = HTTPBearer(auto_error=False, description="Токен ADMIN_API_TOKEN")


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Видати сесію бази даних на час запиту.

    Parameters
    ----------
    request : Request
        Поточний запит; фабрика сесій лежить у app.state.

    Yields
    ------
    AsyncSession
        Відкрита сесія.
    """
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        yield session


def get_app_settings(request: Request) -> Settings:
    """Повернути налаштування застосунку.

    Parameters
    ----------
    request : Request
        Поточний запит.

    Returns
    -------
    Settings
        Налаштування з app.state.
    """
    settings: Settings = request.app.state.settings
    return settings


async def require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> None:
    """Пропустити лише запити з правильним Bearer-токеном адміністратора.

    Parameters
    ----------
    credentials : HTTPAuthorizationCredentials | None
        Дані заголовка Authorization.
    settings : Settings
        Налаштування із очікуваним токеном.

    Raises
    ------
    HTTPException
        401, якщо автентифікації немає; 403, якщо токен неправильний.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Потрібна автентифікація.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not is_valid_admin_token(credentials.credentials, settings.admin_api_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостатньо прав.")

"""Маршрут перевірки готовності."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.schemas.health import HealthResponse
from app.services.container import build_services

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse, "description": "База даних недоступна"}},
)
async def get_health(
    response: Response, session: Annotated[AsyncSession, Depends(get_session)]
) -> HealthResponse:
    """Перевірити готовність застосунку та бази даних.

    Parameters
    ----------
    response : Response
        Відповідь, у якій виставляється код 503 за недоступної БД.
    session : AsyncSession
        Сесія бази даних.

    Returns
    -------
    HealthResponse
        Стан застосунку та БД.
    """
    if await build_services(session).health.is_database_ready():
        return HealthResponse(status="ok", database="ok")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status="unavailable", database="error")

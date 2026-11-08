"""Адміністративні маршрути."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, require_admin
from app.schemas.admin import AdminStatsResponse
from app.services.container import build_services

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    responses={401: {"description": "Немає автентифікації"}, 403: {"description": "Немає прав"}},
)
async def get_stats(session: Annotated[AsyncSession, Depends(get_session)]) -> AdminStatsResponse:
    """Повернути кількість користувачів і записів.

    Parameters
    ----------
    session : AsyncSession
        Сесія бази даних.

    Returns
    -------
    AdminStatsResponse
        Статистика.
    """
    snapshot = await build_services(session).stats.collect()
    return AdminStatsResponse(
        users_count=snapshot.users_count, books_count=snapshot.books_count
    )

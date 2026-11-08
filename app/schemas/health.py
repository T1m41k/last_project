"""Схеми перевірки готовності."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Відповідь GET /health."""

    status: str
    database: str

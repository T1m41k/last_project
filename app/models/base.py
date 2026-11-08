"""Базовий клас ORM-моделей."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовий клас декларативних моделей SQLAlchemy."""

"""Конфігурація застосунку зі змінних середовища."""

from functools import lru_cache
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Налаштування застосунку з environment та файлу .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    admin_api_token: str
    bot_token: str | None = None
    admin_platform_ids: Annotated[list[int], NoDecode] = Field(default_factory=list)
    bot_polling_enabled: bool = True
    log_level: str = "INFO"

    @field_validator("admin_platform_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: object) -> object:
        """Перетворити рядок «1,2,3» на список ідентифікаторів.

        Parameters
        ----------
        value : object
            Сире значення зі змінної середовища або готовий список.

        Returns
        -------
        object
            Список цілих чисел або вихідне значення, якщо воно не рядок.
        """
        if isinstance(value, str):
            return [int(part) for part in value.split(",") if part.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Повернути кешовані налаштування.

    Returns
    -------
    Settings
        Налаштування, прочитані з середовища.
    """
    values: dict[str, Any] = {}
    return Settings(**values)

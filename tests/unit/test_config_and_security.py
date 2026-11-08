"""Модульні тести конфігурації, URL бази даних і перевірки токена."""

import pytest

from app.core.config import Settings, get_settings
from app.core.database import to_async_url
from app.core.security import is_valid_admin_token

ADMIN_KEY = "unit-test-key"


def test_admin_ids_parsed_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """ADMIN_PLATFORM_IDS читається як список чисел через кому."""
    monkeypatch.setenv("ADMIN_PLATFORM_IDS", "5, 6,7")
    settings = Settings(_env_file=None, database_url="postgresql://x/y", admin_api_token=ADMIN_KEY)
    assert settings.admin_platform_ids == [5, 6, 7]


def test_admin_ids_empty_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Без змінної адміністраторів немає."""
    monkeypatch.delenv("ADMIN_PLATFORM_IDS", raising=False)
    settings = Settings(_env_file=None, database_url="postgresql://x/y", admin_api_token=ADMIN_KEY)
    assert settings.admin_platform_ids == []


def test_get_settings_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_settings збирає налаштування зі змінних середовища."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://x/y")
    monkeypatch.setenv("ADMIN_API_TOKEN", ADMIN_KEY)
    get_settings.cache_clear()
    try:
        assert get_settings().database_url == "postgresql://x/y"
    finally:
        get_settings.cache_clear()


def test_to_async_url_keeps_tls() -> None:
    """sslmode перетворюється на ssl, channel_binding відкидається."""
    url = "postgresql://u:p@host.neon.tech/db?sslmode=require&channel_binding=require"
    assert to_async_url(url) == "postgresql+asyncpg://u:p@host.neon.tech/db?ssl=require"


def test_to_async_url_without_query() -> None:
    """URL без параметрів лише змінює драйвер."""
    assert to_async_url("postgresql://u:p@localhost/db") == "postgresql+asyncpg://u:p@localhost/db"


def test_admin_token_comparison() -> None:
    """Токени порівнюються точно."""
    assert is_valid_admin_token(ADMIN_KEY, ADMIN_KEY)
    assert not is_valid_admin_token("інший", ADMIN_KEY)

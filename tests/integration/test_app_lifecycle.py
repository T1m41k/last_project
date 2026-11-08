"""Тести життєвого циклу застосунку (lifespan); БД для них не потрібна."""

import pytest

import app.main as main_module
from app.core.config import Settings


class FakeRuntime:
    """Підроблене середовище бота, що фіксує виклики."""

    def __init__(self) -> None:
        self.events: list[str] = []

    def start(self) -> None:
        """Зафіксувати запуск."""
        self.events.append("start")

    async def stop(self) -> None:
        """Зафіксувати зупинку."""
        self.events.append("stop")


async def test_lifespan_without_bot(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    """Без polling лише готується стан застосунку."""
    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    application = main_module.create_app()
    async with application.router.lifespan_context(application):
        assert application.state.settings is settings
        assert application.state.session_factory is not None


async def test_lifespan_starts_and_stops_bot(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """З увімкненим polling бот запускається та зупиняється разом із застосунком."""
    runtime = FakeRuntime()
    enabled = settings.model_copy(update={"bot_polling_enabled": True})
    monkeypatch.setattr(main_module, "get_settings", lambda: enabled)
    monkeypatch.setattr(main_module, "create_bot_runtime", lambda *_: runtime)
    application = main_module.create_app()
    async with application.router.lifespan_context(application):
        assert runtime.events == ["start"]
    assert runtime.events == ["start", "stop"]

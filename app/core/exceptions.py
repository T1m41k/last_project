"""Власні винятки застосунку."""


class AppError(Exception):
    """Базовий виняток; його текст безпечно показувати користувачу."""


class ValidationFailedError(AppError):
    """Введене значення має неприпустимий тип або довжину."""


class BookNotFoundError(AppError):
    """Запис не існує або належить іншому користувачу."""


class PlatformError(AppError):
    """Помилка або тайм-аут під час виклику API платформи."""


class ConfigurationError(AppError):
    """Невірна або відсутня конфігурація."""

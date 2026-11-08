"""Перевірка токена адміністратора."""

import secrets


def is_valid_admin_token(provided: str, expected: str) -> bool:
    """Порівняти токени за постійний час.

    Parameters
    ----------
    provided : str
        Токен із заголовка Authorization.
    expected : str
        Токен із конфігурації.

    Returns
    -------
    bool
        True, якщо токени збігаються.
    """
    return secrets.compare_digest(provided.encode(), expected.encode())

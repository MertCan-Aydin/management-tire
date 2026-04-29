"""
Token'ları OS keychain'de saklar (Windows DPAPI / macOS Keychain).
Düz dosyaya / registrye token yazmak yasak.
"""

import keyring
from .config import TOKEN_SERVICE

_ACCESS_KEY = "access_token"
_REFRESH_KEY = "refresh_token"


def save_tokens(access: str, refresh: str) -> None:
    keyring.set_password(TOKEN_SERVICE, _ACCESS_KEY, access)
    keyring.set_password(TOKEN_SERVICE, _REFRESH_KEY, refresh)


def get_access_token() -> str | None:
    return keyring.get_password(TOKEN_SERVICE, _ACCESS_KEY)


def get_refresh_token() -> str | None:
    return keyring.get_password(TOKEN_SERVICE, _REFRESH_KEY)


def clear_tokens() -> None:
    try:
        keyring.delete_password(TOKEN_SERVICE, _ACCESS_KEY)
    except keyring.errors.PasswordDeleteError:
        pass
    try:
        keyring.delete_password(TOKEN_SERVICE, _REFRESH_KEY)
    except keyring.errors.PasswordDeleteError:
        pass

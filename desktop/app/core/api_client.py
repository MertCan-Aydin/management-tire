"""
Tüm HTTP istekleri buradan geçer.
Token yönetimi, hata çevirisi ve retry burada yapılır.
"""

import requests
from requests.exceptions import ConnectionError, Timeout

from .config import API_BASE_URL
from .token_store import get_access_token, get_refresh_token, save_tokens, clear_tokens

_SESSION = requests.Session()
_SESSION.headers.update({"Content-Type": "application/json"})


class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class AuthError(APIError):
    pass


class NetworkError(Exception):
    pass


def _url(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def _handle_response(resp: requests.Response):
    if resp.status_code == 401:
        raise AuthError(401, "Oturum süresi doldu, lütfen tekrar giriş yapın.")
    if not resp.ok:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise APIError(resp.status_code, detail)
    if resp.status_code == 204 or not resp.content:
        return None
    return resp.json()


def _auth_header() -> dict:
    token = get_access_token()
    return {"Authorization": f"Bearer {token}"} if token else {}


def _request(method: str, path: str, *, retry_auth: bool = True, **kwargs):
    try:
        resp = _SESSION.request(
            method,
            _url(path),
            headers=_auth_header(),
            timeout=15,
            verify=True,   # SSL doğrulama HER ZAMAN açık
            **kwargs,
        )
    except (ConnectionError, Timeout) as e:
        raise NetworkError(f"Sunucuya ulaşılamıyor: {e}") from e

    if resp.status_code == 401 and retry_auth:
        # Access token süresi dolmuş, refresh dene
        refreshed = _try_refresh()
        if refreshed:
            return _request(method, path, retry_auth=False, **kwargs)
        clear_tokens()
        raise AuthError(401, "Oturum süresi doldu.")

    return _handle_response(resp)


def _try_refresh() -> bool:
    raw_refresh = get_refresh_token()
    if not raw_refresh:
        return False
    try:
        resp = _SESSION.post(
            _url("/api/auth/yenile"),
            json={"refresh_token": raw_refresh},
            timeout=10,
            verify=True,
        )
        if resp.ok:
            data = resp.json()
            save_tokens(data["access_token"], data["refresh_token"])
            return True
    except Exception:
        pass
    return False


def get(path: str, params: dict = None):
    return _request("GET", path, params=params)


def post(path: str, json: dict = None):
    return _request("POST", path, json=json)


def put(path: str, json: dict = None):
    return _request("PUT", path, json=json)


def delete(path: str, params: dict = None):
    return _request("DELETE", path, params=params)


def login(kullanici_adi: str, parola: str) -> dict:
    """OAuth2 password flow — form-encoded."""
    try:
        resp = _SESSION.post(
            _url("/api/auth/giris"),
            data={"username": kullanici_adi, "password": parola},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
            verify=True,
        )
    except (ConnectionError, Timeout) as e:
        raise NetworkError(f"Sunucuya ulaşılamıyor: {e}") from e

    return _handle_response(resp)


def pin_login(pin: str) -> dict:
    """Sadece PIN ile giriş yap."""
    return post("/api/auth/pin-giris", json={"pin": pin})


def get_setup_status() -> bool:
    """Sistemin kurulu olup olmadığını (admin var mı) kontrol et."""
    data = get("/api/auth/setup-durumu")
    return data.get("kurulu_mu", False)


def setup_pin(pin: str) -> dict:
    """İlk PIN kurulumunu yap."""
    return post("/api/auth/pin-kurulum", json={"pin": pin})


def logout(raw_refresh: str) -> None:
    try:
        _request("POST", "/api/auth/cikis", json={"refresh_token": raw_refresh}, retry_auth=False)
    except Exception:
        pass
    clear_tokens()

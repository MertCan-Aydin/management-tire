from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from ..core.db import get_cursor
from ..core.security import decode_access_token
from ..business import auth_service
from ..data_access import auth_dal
from ..schemas.auth import (
    TokenResponse, RefreshRequest, ParolaDegistirRequest, 
    KullaniciBilgi, PinLoginRequest
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/giris")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"id": int(payload["sub"]), "rol": payload["rol"]}


@router.get("/setup-durumu")
def setup_durumu():
    """Sistemde kurulu bir admin olup olmadığını döner."""
    with get_cursor() as (cursor, _):
        admin = auth_dal.admin_kullanici_getir(cursor)
    return {"kurulu_mu": admin is not None}


@router.post("/pin-kurulum", response_model=TokenResponse)
def pin_kurulum(body: PinLoginRequest):
    """Sistem ilk kurulduğunda admin PIN'ini oluşturur."""
    with get_cursor() as (cursor, _):
        # Güvenlik: Zaten admin varsa kuruluma izin verme
        mevcut = auth_dal.admin_kullanici_getir(cursor)
        if mevcut:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sistem zaten kurulu."
            )
        return auth_service.pin_kurulum_yap(cursor, body.pin)


@router.post("/pin-giris", response_model=TokenResponse)
def pin_giris(body: PinLoginRequest):
    """Sadece PIN ile giriş yap."""
    with get_cursor() as (cursor, _):
        return auth_service.pin_giris(cursor, body.pin)


@router.post("/giris", response_model=TokenResponse)
def giris(form: OAuth2PasswordRequestForm = Depends()):
    with get_cursor() as (cursor, _):
        return auth_service.giris_yap(cursor, form.username, form.password)


@router.post("/yenile", response_model=TokenResponse)
def token_yenile(body: RefreshRequest):
    with get_cursor() as (cursor, _):
        return auth_service.token_yenile(cursor, body.refresh_token)


@router.post("/cikis")
def cikis(body: RefreshRequest):
    with get_cursor() as (cursor, _):
        auth_service.cikis_yap(cursor, body.refresh_token)
    return {"mesaj": "Çıkış yapıldı"}


@router.post("/parola-degistir")
def parola_degistir(
    body: ParolaDegistirRequest,
    current_user: dict = Depends(get_current_user),
):
    with get_cursor() as (cursor, _):
        auth_service.parola_degistir(cursor, current_user["id"], body.mevcut_parola, body.yeni_parola)
    return {"mesaj": "Parola güncellendi"}


@router.get("/ben", response_model=KullaniciBilgi)
def ben(current_user: dict = Depends(get_current_user)):
    with get_cursor() as (cursor, _):
        kullanici = auth_dal.kullanici_getir(cursor, current_user["id"])
    if not kullanici:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return kullanici

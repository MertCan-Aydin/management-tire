from fastapi import HTTPException, status

from ..core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from ..data_access import auth_dal


def pin_kurulum_yap(cursor, pin: str) -> dict:
    """İlk kurulum: admin kullanıcısını oluşturur ve PIN'i set eder."""
    # Varsayılan admin kullanıcı adı 'admin'
    hashli_pin = hash_password(pin)
    kullanici_id = auth_dal.kullanici_olustur(cursor, "admin", hashli_pin, "admin")
    
    auth_dal.giris_tarihi_guncelle(cursor, kullanici_id)
    access = create_access_token(kullanici_id, "admin")
    raw_refresh, token_hash, expiry = create_refresh_token()
    auth_dal.refresh_token_ekle(cursor, kullanici_id, token_hash, expiry)
    return {"access_token": access, "refresh_token": raw_refresh}


def pin_giris(cursor, pin: str) -> dict:
    """Tek kullanıcılı PIN login — kullanıcı adı sorulmaz."""
    kullanici = auth_dal.admin_kullanici_getir(cursor)
    # Hata mesajı belirsiz — timing attack + enumeration koruması
    if not kullanici or not verify_password(pin, kullanici["parola_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN hatalı",
        )
    auth_dal.giris_tarihi_guncelle(cursor, kullanici["id"])
    access = create_access_token(kullanici["id"], kullanici["rol"])
    raw_refresh, token_hash, expiry = create_refresh_token()
    auth_dal.refresh_token_ekle(cursor, kullanici["id"], token_hash, expiry)
    return {"access_token": access, "refresh_token": raw_refresh}


def giris_yap(cursor, kullanici_adi: str, parola: str) -> dict:
    kullanici = auth_dal.kullanici_adi_ile_getir(cursor, kullanici_adi)
    # Hata mesajı kasıtlı belirsiz — user enumeration koruması
    if not kullanici or not verify_password(parola, kullanici["parola_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya parola hatalı",
        )
    auth_dal.giris_tarihi_guncelle(cursor, kullanici["id"])
    access = create_access_token(kullanici["id"], kullanici["rol"])
    raw_refresh, token_hash, expiry = create_refresh_token()
    auth_dal.refresh_token_ekle(cursor, kullanici["id"], token_hash, expiry)
    return {"access_token": access, "refresh_token": raw_refresh}


def token_yenile(cursor, raw_refresh: str) -> dict:
    token_hash = hash_refresh_token(raw_refresh)
    kayit = auth_dal.refresh_token_getir(cursor, token_hash)
    if not kayit:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token",
        )
    auth_dal.refresh_token_iptal(cursor, token_hash)
    kullanici = auth_dal.kullanici_getir(cursor, kayit["kullanici_id"])
    if not kullanici:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kullanıcı bulunamadı")
    access = create_access_token(kullanici["id"], kullanici["rol"])
    raw_new, new_hash, expiry = create_refresh_token()
    auth_dal.refresh_token_ekle(cursor, kullanici["id"], new_hash, expiry)
    return {"access_token": access, "refresh_token": raw_new}


def cikis_yap(cursor, raw_refresh: str) -> None:
    token_hash = hash_refresh_token(raw_refresh)
    auth_dal.refresh_token_iptal(cursor, token_hash)


def parola_degistir(cursor, kullanici_id: int, mevcut: str, yeni: str) -> None:
    kullanici = auth_dal.kullanici_getir(cursor, kullanici_id)
    if not kullanici:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı")
    tam_kullanici = auth_dal.kullanici_adi_ile_getir(cursor, kullanici["kullanici_adi"])
    if not verify_password(mevcut, tam_kullanici["parola_hash"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mevcut parola hatalı")
    auth_dal.parola_guncelle(cursor, kullanici_id, hash_password(yeni))
    auth_dal.tum_tokenlari_iptal(cursor, kullanici_id)

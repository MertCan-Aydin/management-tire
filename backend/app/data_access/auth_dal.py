from datetime import datetime

from ..core.db import call_sp, call_sp_one


def admin_kullanici_getir(cursor) -> dict | None:
    """PIN login için — sistemdeki tek admin kullanıcıyı döner."""
    return call_sp_one(cursor, "sp_admin_kullanici_getir")


def kullanici_adi_ile_getir(cursor, kullanici_adi: str) -> dict | None:
    return call_sp_one(cursor, "sp_kullanici_adi_ile_getir", [kullanici_adi])


def kullanici_getir(cursor, kullanici_id: int) -> dict | None:
    return call_sp_one(cursor, "sp_kullanici_getir", [kullanici_id])


def kullanici_olustur(cursor, kullanici_adi: str, parola_hash: str, rol: str) -> int:
    row = call_sp_one(cursor, "sp_kullanici_olustur", [kullanici_adi, parola_hash, rol])
    return row["id"] if row else None


def giris_tarihi_guncelle(cursor, kullanici_id: int) -> None:
    call_sp(cursor, "sp_kullanici_giris_tarihi_guncelle", [kullanici_id])


def parola_guncelle(cursor, kullanici_id: int, yeni_hash: str) -> None:
    call_sp(cursor, "sp_kullanici_parola_guncelle", [kullanici_id, yeni_hash])


def refresh_token_ekle(cursor, kullanici_id: int, token_hash: str, son_kullanma: datetime) -> None:
    call_sp(cursor, "sp_refresh_token_ekle", [kullanici_id, token_hash, son_kullanma])


def refresh_token_getir(cursor, token_hash: str) -> dict | None:
    return call_sp_one(cursor, "sp_refresh_token_getir", [token_hash])


def refresh_token_iptal(cursor, token_hash: str) -> None:
    call_sp(cursor, "sp_refresh_token_iptal", [token_hash])


def tum_tokenlari_iptal(cursor, kullanici_id: int) -> None:
    call_sp(cursor, "sp_refresh_tokenlari_kullaniciya_gore_iptal", [kullanici_id])

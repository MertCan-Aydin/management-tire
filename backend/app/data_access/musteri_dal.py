from ..core.db import call_sp, call_sp_one


def listele(cursor, arama, limit, offset) -> list:
    return call_sp(cursor, "sp_musteriler_listele", [arama, limit, offset])


def getir(cursor, musteri_id: int) -> dict | None:
    return call_sp_one(cursor, "sp_musteriler_getir", [musteri_id])


def plaka_ara(cursor, plaka: str) -> dict | None:
    return call_sp_one(cursor, "sp_musteriler_plaka_ara", [plaka])


def telefon_ara(cursor, telefon: str) -> dict | None:
    return call_sp_one(cursor, "sp_musteriler_telefon_ara", [telefon])


def ekle(cursor, ad_soyad, telefon, arac_markasi, arac_plakasi, notlar) -> int:
    row = call_sp_one(cursor, "sp_musteriler_ekle", [ad_soyad, telefon, arac_markasi, arac_plakasi, notlar])
    return row["id"] if row else None


def guncelle(cursor, mid, ad_soyad, telefon, arac_markasi, arac_plakasi, notlar) -> None:
    call_sp(cursor, "sp_musteriler_guncelle", [mid, ad_soyad, telefon, arac_markasi, arac_plakasi, notlar])


def sil(cursor, musteri_id: int) -> None:
    call_sp(cursor, "sp_musteriler_sil", [musteri_id])

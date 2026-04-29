from fastapi import HTTPException

from ..data_access import musteri_dal


def listele(cursor, arama, limit, offset) -> list:
    return musteri_dal.listele(cursor, arama, limit, offset)


def getir(cursor, mid: int) -> dict:
    m = musteri_dal.getir(cursor, mid)
    if not m:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    return m


def ekle(cursor, data) -> int:
    return musteri_dal.ekle(cursor, data.ad_soyad, data.telefon, data.arac_markasi, data.arac_plakasi, data.notlar)


def guncelle(cursor, mid: int, data) -> None:
    getir(cursor, mid)
    musteri_dal.guncelle(cursor, mid, data.ad_soyad, data.telefon, data.arac_markasi, data.arac_plakasi, data.notlar)


def sil(cursor, mid: int) -> None:
    getir(cursor, mid)
    musteri_dal.sil(cursor, mid)


def plaka_ara(cursor, plaka: str) -> dict:
    m = musteri_dal.plaka_ara(cursor, plaka)
    if not m:
        raise HTTPException(status_code=404, detail="Bu plakaya ait müşteri bulunamadı")
    return m

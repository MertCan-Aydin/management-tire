from fastapi import HTTPException
from ..data_access import taslak_dal


def listele(cursor, kullanici_id, form_tipi=None) -> list:
    return taslak_dal.listele(cursor, kullanici_id, form_tipi)


def getir(cursor, taslak_id) -> dict:
    t = taslak_dal.getir(cursor, taslak_id)
    if not t:
        raise HTTPException(status_code=404, detail="Taslak bulunamadı")
    return t


def ekle(cursor, kullanici_id, form_tipi, baslik, veri) -> int:
    return taslak_dal.ekle(cursor, kullanici_id, form_tipi, baslik, veri)


def guncelle(cursor, taslak_id, baslik, veri) -> None:
    getir(cursor, taslak_id)
    taslak_dal.guncelle(cursor, taslak_id, baslik, veri)


def sil(cursor, taslak_id) -> None:
    getir(cursor, taslak_id)
    taslak_dal.sil(cursor, taslak_id)

from fastapi import HTTPException

from ..data_access import gider_dal


def listele(cursor, baslangic, bitis, limit, offset) -> list:
    return gider_dal.listele(cursor, baslangic, bitis, limit, offset)


def getir(cursor, gid: int) -> dict:
    g = gider_dal.getir(cursor, gid)
    if not g:
        raise HTTPException(status_code=404, detail="Gider bulunamadı")
    return g


def ekle(cursor, data) -> int:
    return gider_dal.ekle(cursor, data.aciklama, data.tutar)


def guncelle(cursor, gid: int, data) -> None:
    getir(cursor, gid)
    gider_dal.guncelle(cursor, gid, data.aciklama, data.tutar, data.tarih)


def sil(cursor, gid: int) -> None:
    getir(cursor, gid)
    gider_dal.sil(cursor, gid)

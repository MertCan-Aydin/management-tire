from fastapi import HTTPException

from ..data_access import musteri_dal, satis_dal


def listele(cursor, baslangic, bitis, musteri_id, odeme_yontemi, limit, offset) -> list:
    return satis_dal.listele(cursor, baslangic, bitis, musteri_id, odeme_yontemi, limit, offset)


def getir(cursor, satis_id: int) -> dict:
    s = satis_dal.getir(cursor, satis_id)
    if not s:
        raise HTTPException(status_code=404, detail="Satış bulunamadı")
    return {**s, "kalemler": satis_dal.kalemler_listele(cursor, satis_id)}


def ekle(cursor, data) -> int:
    if not musteri_dal.getir(cursor, data.musteri_id):
        raise HTTPException(status_code=400, detail="Müşteri bulunamadı veya silinmiş")
    satis_id = satis_dal.ekle(cursor, data.musteri_id, data.odeme_yontemi, 0, 0, data.indirim)
    for kalem in data.kalemler:
        satis_dal.kalem_ekle(cursor, satis_id, kalem.urun_id, kalem.urun_adi_anlik, kalem.miktar, kalem.birim_fiyat, kalem.birim_maliyet)
    return satis_id


def iptal(cursor, satis_id: int) -> None:
    _varmi(cursor, satis_id)
    satis_dal.iptal(cursor, satis_id)


def kalem_iptal(cursor, kalem_id: int) -> None:
    satis_dal.kalem_iptal(cursor, kalem_id)


def _varmi(cursor, satis_id: int):
    if not satis_dal.getir(cursor, satis_id):
        raise HTTPException(status_code=404, detail="Satış bulunamadı")

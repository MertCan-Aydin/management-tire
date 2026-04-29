from fastapi import HTTPException

from ..data_access import alim_dal


def listele(cursor, baslangic, bitis, tedarikci_id, limit, offset) -> list:
    return alim_dal.listele(cursor, baslangic, bitis, tedarikci_id, limit, offset)


def getir(cursor, alim_id: int) -> dict:
    a = alim_dal.getir(cursor, alim_id)
    if not a:
        raise HTTPException(status_code=404, detail="Alım bulunamadı")
    return {**a, "kalemler": alim_dal.kalemler_listele(cursor, alim_id)}


def ekle(cursor, data) -> int:
    alim_id = alim_dal.ekle(cursor, data.tedarikci_id, 0)
    for kalem in data.kalemler:
        alim_dal.kalem_ekle(cursor, alim_id, kalem.urun_id, kalem.urun_adi_anlik, kalem.miktar, kalem.birim_fiyat)
    return alim_id


def iptal(cursor, alim_id: int) -> None:
    _varmi(cursor, alim_id)
    alim_dal.iptal(cursor, alim_id)


def _varmi(cursor, alim_id: int):
    if not alim_dal.getir(cursor, alim_id):
        raise HTTPException(status_code=404, detail="Alım bulunamadı")

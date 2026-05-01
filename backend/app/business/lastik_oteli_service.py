from fastapi import HTTPException, status
from ..data_access import lastik_oteli_dal


def listele(cursor, sadece_aktif: bool, arama: str, limit: int, offset: int) -> list:
    return lastik_oteli_dal.listele(cursor, sadece_aktif, arama, limit, offset)


def getir(cursor, kayit_id: int) -> dict:
    kayit = lastik_oteli_dal.getir(cursor, kayit_id)
    if not kayit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Kayıt bulunamadı")
    return kayit


def ekle(cursor, req) -> dict:
    try:
        yeni_id = lastik_oteli_dal.ekle(cursor, {
            "musteri_id":        req.musteri_id,
            "musteri_adi_anlik": req.musteri_adi_anlik,
            "arac_plakasi":      req.arac_plakasi,
            "raf_kodu":          req.raf_kodu,
            "lastik_bilgisi":    req.lastik_bilgisi,
            "lastik_adedi":      req.lastik_adedi,
            "sezon":             req.sezon,
            "giris_tarihi":      req.giris_tarihi,
            "notlar":            req.notlar,
        })
    except Exception as e:
        msg = str(e)
        if "zaten dolu" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise
    return {"id": yeni_id, "mesaj": "Lastik oteline eklendi"}


def teslim_et(cursor, kayit_id: int, cikis_tarihi) -> None:
    _varmi(cursor, kayit_id)
    lastik_oteli_dal.teslim_et(cursor, kayit_id, cikis_tarihi)


def sil(cursor, kayit_id: int) -> None:
    _varmi(cursor, kayit_id)
    lastik_oteli_dal.sil(cursor, kayit_id)


def raf_sorgula(cursor, raf_kodu: str) -> dict | None:
    return lastik_oteli_dal.raf_kontrol(cursor, raf_kodu.upper())


def _varmi(cursor, kayit_id: int):
    if not lastik_oteli_dal.getir(cursor, kayit_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Kayıt bulunamadı")

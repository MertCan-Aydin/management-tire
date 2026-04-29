from fastapi import HTTPException, status

from ..data_access import urun_dal


def tipleri_listele(cursor) -> list:
    return urun_dal.urun_tipleri_listele(cursor)


def tip_ekle(cursor, ad: str) -> None:
    urun_dal.urun_tipi_ekle(cursor, ad)


def tip_guncelle(cursor, tip_id: int, ad: str) -> None:
    _tip_varmi(cursor, tip_id)
    urun_dal.urun_tipi_guncelle(cursor, tip_id, ad)


def tip_sil(cursor, tip_id: int) -> None:
    _tip_varmi(cursor, tip_id)
    urun_dal.urun_tipi_sil(cursor, tip_id)


def markalari_listele(cursor, tip_id: int | None) -> list:
    if tip_id:
        return urun_dal.markalar_tipe_gore_listele(cursor, tip_id)
    return urun_dal.markalar_listele(cursor)


def marka_ekle(cursor, tip_id: int, ad: str) -> None:
    urun_dal.marka_ekle(cursor, tip_id, ad)


def marka_guncelle(cursor, marka_id: int, tip_id: int, ad: str) -> None:
    _marka_varmi(cursor, marka_id)
    urun_dal.marka_guncelle(cursor, marka_id, tip_id, ad)


def marka_sil(cursor, marka_id: int) -> None:
    _marka_varmi(cursor, marka_id)
    urun_dal.marka_sil(cursor, marka_id)


def modelleri_listele(cursor, marka_id: int | None) -> list:
    if marka_id:
        return urun_dal.modeller_markaya_gore_listele(cursor, marka_id)
    return urun_dal.modeller_listele(cursor)


def model_ekle(cursor, marka_id: int, ad: str, mevsim) -> None:
    urun_dal.model_ekle(cursor, marka_id, ad, mevsim)


def model_guncelle(cursor, model_id: int, marka_id: int, ad: str, mevsim) -> None:
    _model_varmi(cursor, model_id)
    urun_dal.model_guncelle(cursor, model_id, marka_id, ad, mevsim)


def model_sil(cursor, model_id: int) -> None:
    _model_varmi(cursor, model_id)
    urun_dal.model_sil(cursor, model_id)


def urunleri_listele(cursor, filtre) -> list:
    return urun_dal.urunler_listele(
        cursor,
        filtre.arama, filtre.urun_tipi_id, filtre.marka_id,
        filtre.sadece_stoklu, filtre.limit, filtre.offset,
    )


def urun_getir(cursor, urun_id: int) -> dict:
    urun = urun_dal.urun_getir(cursor, urun_id)
    if not urun:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ürün bulunamadı")
    return urun


def barkod_ara(cursor, barkod: str) -> dict:
    urun = urun_dal.urun_barkod_ara(cursor, barkod)
    if not urun:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bu barkoda sahip ürün bulunamadı")
    return urun


def urun_ekle(cursor, data: dict) -> int:
    return urun_dal.urun_ekle(cursor, data)


def urun_guncelle(cursor, urun_id: int, data: dict) -> None:
    _urun_varmi(cursor, urun_id)
    urun_dal.urun_guncelle(cursor, urun_id, data)


def urun_sil(cursor, urun_id: int) -> None:
    _urun_varmi(cursor, urun_id)
    urun_dal.urun_sil(cursor, urun_id)


# --- Guard yardımcılar ---

def _tip_varmi(cursor, tip_id: int):
    if not urun_dal.urun_tipi_getir(cursor, tip_id):
        raise HTTPException(status_code=404, detail="Ürün tipi bulunamadı")


def _marka_varmi(cursor, marka_id: int):
    if not urun_dal.marka_getir(cursor, marka_id):
        raise HTTPException(status_code=404, detail="Marka bulunamadı")


def _model_varmi(cursor, model_id: int):
    if not urun_dal.model_getir(cursor, model_id):
        raise HTTPException(status_code=404, detail="Model bulunamadı")


def _urun_varmi(cursor, urun_id: int):
    if not urun_dal.urun_getir(cursor, urun_id):
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")

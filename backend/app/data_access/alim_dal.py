from ..core.db import call_sp, call_sp_one


def listele(cursor, baslangic, bitis, tedarikci_id, limit, offset) -> list:
    return call_sp(cursor, "sp_alimlar_listele", [baslangic, bitis, tedarikci_id, limit, offset])


def getir(cursor, alim_id: int) -> dict | None:
    return call_sp_one(cursor, "sp_alimlar_getir", [alim_id])


def ekle(cursor, tedarikci_id: int, toplam_tutar: float) -> int:
    row = call_sp_one(cursor, "sp_alimlar_ekle", [tedarikci_id, toplam_tutar])
    return row["id"] if row else None


def iptal(cursor, alim_id: int) -> None:
    call_sp(cursor, "sp_alimlar_sil", [alim_id])


def kalem_ekle(cursor, alim_id, urun_id, urun_adi, miktar, birim_fiyat) -> int:
    row = call_sp_one(cursor, "sp_alim_kalemleri_ekle", [alim_id, urun_id, urun_adi, miktar, birim_fiyat])
    return row["id"] if row else None


def kalemler_listele(cursor, alim_id: int) -> list:
    return call_sp(cursor, "sp_alim_kalemleri_alima_gore_listele", [alim_id])

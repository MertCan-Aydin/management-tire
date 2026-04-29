from ..core.db import call_sp, call_sp_one


def listele(cursor, baslangic, bitis, musteri_id, odeme_yontemi, limit, offset) -> list:
    return call_sp(cursor, "sp_satislar_listele", [baslangic, bitis, musteri_id, odeme_yontemi, limit, offset])


def getir(cursor, satis_id: int) -> dict | None:
    return call_sp_one(cursor, "sp_satislar_getir", [satis_id])


def ekle(cursor, musteri_id, odeme_yontemi, toplam_tutar, toplam_maliyet, indirim) -> int:
    row = call_sp_one(cursor, "sp_satislar_ekle", [musteri_id, odeme_yontemi, toplam_tutar, toplam_maliyet, indirim])
    return row["id"] if row else None


def iptal(cursor, satis_id: int) -> None:
    call_sp(cursor, "sp_satislar_sil", [satis_id])


def kalem_ekle(cursor, satis_id, urun_id, urun_adi, miktar, birim_fiyat, birim_maliyet) -> int:
    row = call_sp_one(cursor, "sp_satis_kalemleri_ekle", [satis_id, urun_id, urun_adi, miktar, birim_fiyat, birim_maliyet])
    return row["id"] if row else None


def kalemler_listele(cursor, satis_id: int) -> list:
    return call_sp(cursor, "sp_satis_kalemleri_satisa_gore_listele", [satis_id])


def kalem_iptal(cursor, kalem_id: int) -> None:
    call_sp(cursor, "sp_satis_kalemleri_sil", [kalem_id])

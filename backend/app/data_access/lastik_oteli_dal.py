from ..core.db import call_sp, call_sp_one


def listele(cursor, sadece_aktif: bool, arama: str, limit: int, offset: int) -> list:
    return call_sp(cursor, "sp_lastik_oteli_listele",
                   [int(sadece_aktif), arama or "", limit, offset])


def getir(cursor, kayit_id: int) -> dict | None:
    return call_sp_one(cursor, "sp_lastik_oteli_getir", [kayit_id])


def ekle(cursor, data: dict) -> int:
    row = call_sp_one(cursor, "sp_lastik_oteli_ekle", [
        data["musteri_id"],
        data["musteri_adi_anlik"],
        data["arac_plakasi"],
        data["raf_kodu"],
        data["lastik_bilgisi"],
        data["lastik_adedi"],
        data["sezon"],
        data["giris_tarihi"],
        data["notlar"],
    ])
    return row["id"] if row else None


def teslim_et(cursor, kayit_id: int, cikis_tarihi) -> None:
    call_sp(cursor, "sp_lastik_oteli_teslim_et", [kayit_id, cikis_tarihi])


def sil(cursor, kayit_id: int) -> None:
    call_sp(cursor, "sp_lastik_oteli_sil", [kayit_id])


def raf_kontrol(cursor, raf_kodu: str) -> dict | None:
    return call_sp_one(cursor, "sp_lastik_oteli_raf_kontrol", [raf_kodu])

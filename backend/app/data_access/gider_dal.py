from ..core.db import call_sp, call_sp_one


def listele(cursor, baslangic, bitis, limit, offset) -> list:
    return call_sp(cursor, "sp_giderler_listele", [baslangic, bitis, limit, offset])


def getir(cursor, gider_id: int) -> dict | None:
    return call_sp_one(cursor, "sp_giderler_getir", [gider_id])


def ekle(cursor, aciklama: str, tutar: float) -> int:
    row = call_sp_one(cursor, "sp_giderler_ekle", [aciklama, tutar])
    return row["id"] if row else None


def guncelle(cursor, gid, aciklama, tutar, tarih) -> None:
    call_sp(cursor, "sp_giderler_guncelle", [gid, aciklama, tutar, tarih])


def sil(cursor, gider_id: int) -> None:
    call_sp(cursor, "sp_giderler_sil", [gider_id])

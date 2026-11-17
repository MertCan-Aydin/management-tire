from ..core.db import call_sp, call_sp_one


def listele(cursor, baslangic, bitis, limit, offset, kategori=None) -> list:
    return call_sp(cursor, "sp_giderler_listele", [baslangic, bitis, limit, offset, kategori])


def getir(cursor, gider_id: int) -> dict | None:
    return call_sp_one(cursor, "sp_giderler_getir", [gider_id])


def ekle(cursor, data) -> int:
    row = call_sp_one(cursor, "sp_giderler_ekle", [
        data.aciklama, data.tutar, data.kategori,
        data.urun_adi, data.marka, data.alis_fiyati,
        data.satis_fiyati, data.yil, int(data.maliyet_bilinmiyor),
    ])
    return row["id"] if row else None


def guncelle(cursor, gid, data) -> None:
    call_sp(cursor, "sp_giderler_guncelle", [
        gid, data.aciklama, data.tutar, data.tarih,
        data.kategori, data.urun_adi, data.marka,
        data.alis_fiyati, data.satis_fiyati, data.yil,
        int(data.maliyet_bilinmiyor),
    ])


def sil(cursor, gider_id: int) -> None:
    call_sp(cursor, "sp_giderler_sil", [gider_id])

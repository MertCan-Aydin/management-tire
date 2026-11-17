from ..core.db import call_sp, call_sp_one


def log_ekle(cursor, kullanici_id, islem_tipi, sayfa, detay, ip_adresi) -> int:
    row = call_sp_one(cursor, "sp_aktivite_log_ekle", [
        kullanici_id, islem_tipi, sayfa, detay, ip_adresi,
    ])
    return row["id"] if row else None


def log_listele(cursor, kullanici_id, islem_tipi, baslangic, bitis, limit, offset) -> list:
    return call_sp(cursor, "sp_aktivite_log_listele", [
        kullanici_id, islem_tipi, baslangic, bitis, limit, offset,
    ])

import json
from ..core.db import call_sp, call_sp_one


def ekle(cursor, kullanici_id, form_tipi, baslik, veri) -> int:
    row = call_sp_one(cursor, "sp_taslak_ekle", [
        kullanici_id, form_tipi, baslik, json.dumps(veri, ensure_ascii=False),
    ])
    return row["id"] if row else None


def guncelle(cursor, taslak_id, baslik, veri) -> None:
    call_sp(cursor, "sp_taslak_guncelle", [
        taslak_id, baslik, json.dumps(veri, ensure_ascii=False),
    ])


def listele(cursor, kullanici_id, form_tipi=None) -> list:
    rows = call_sp(cursor, "sp_taslak_listele", [kullanici_id, form_tipi])
    for r in rows:
        if isinstance(r.get("veri"), str):
            r["veri"] = json.loads(r["veri"])
    return rows


def getir(cursor, taslak_id) -> dict | None:
    r = call_sp_one(cursor, "sp_taslak_getir", [taslak_id])
    if r and isinstance(r.get("veri"), str):
        r["veri"] = json.loads(r["veri"])
    return r


def sil(cursor, taslak_id) -> None:
    call_sp(cursor, "sp_taslak_sil", [taslak_id])

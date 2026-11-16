from ..core.db import call_sp, call_sp_one


def markalar_listele(cursor) -> list:
    return call_sp(cursor, "sp_lastik_markalari_listele")


def marka_ekle(cursor, ad: str) -> int:
    row = call_sp_one(cursor, "sp_lastik_markalari_ekle", [ad])
    return row["id"] if row else 0


def modeller_listele(cursor) -> list:
    return call_sp(cursor, "sp_lastik_modelleri_listele")


def model_ekle(cursor, ad: str) -> int:
    row = call_sp_one(cursor, "sp_lastik_modelleri_ekle", [ad])
    return row["id"] if row else 0


def ebatlar_listele(cursor, kategori: str | None = None) -> list:
    return call_sp(cursor, "sp_lastik_ebatlari_listele", [kategori or ""])


def ebat_ekle(cursor, ebat: str, kategori: str) -> int:
    row = call_sp_one(cursor, "sp_lastik_ebatlari_ekle", [ebat, kategori])
    return row["id"] if row else 0

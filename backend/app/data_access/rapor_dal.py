from ..core.db import call_sp, call_sp_one


def dashboard_ozet(cursor) -> dict | None:
    return call_sp_one(cursor, "sp_dashboard_ozet")


def gunluk_rapor(cursor, tarih: str) -> dict | None:
    return call_sp_one(cursor, "sp_rapor_gunluk", [tarih])


def aralik_rapor(cursor, baslangic: str, bitis: str) -> dict | None:
    return call_sp_one(cursor, "sp_rapor_aralik", [baslangic, bitis])


def gunluk_kirilim(cursor, baslangic: str, bitis: str) -> list:
    return call_sp(cursor, "sp_rapor_gunluk_kirilim", [baslangic, bitis])


def en_cok_satan(cursor, baslangic: str, bitis: str, limit: int) -> list:
    return call_sp(cursor, "sp_rapor_en_cok_satan", [baslangic, bitis, limit])


def tedarikci_alim(cursor, baslangic: str, bitis: str) -> list:
    return call_sp(cursor, "sp_rapor_tedarikci_alim", [baslangic, bitis])

from ..data_access import rapor_dal


def dashboard(cursor) -> dict:
    return rapor_dal.dashboard_ozet(cursor) or {}


def gunluk(cursor, tarih: str) -> dict:
    return rapor_dal.gunluk_rapor(cursor, tarih) or {}


def aralik(cursor, baslangic: str, bitis: str) -> dict:
    return rapor_dal.aralik_rapor(cursor, baslangic, bitis) or {}


def gunluk_kirilim(cursor, baslangic: str, bitis: str) -> list:
    return rapor_dal.gunluk_kirilim(cursor, baslangic, bitis)


def en_cok_satan(cursor, baslangic: str, bitis: str, limit: int) -> list:
    return rapor_dal.en_cok_satan(cursor, baslangic, bitis, limit)


def tedarikci_alim(cursor, baslangic: str, bitis: str) -> list:
    return rapor_dal.tedarikci_alim(cursor, baslangic, bitis)

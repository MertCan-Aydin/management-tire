from ..core.db import call_sp, call_sp_one


def tedarikciler_listele(cursor) -> list:
    return call_sp(cursor, "sp_tedarikciler_listele")


def tedarikci_getir(cursor, tedarikci_id: int) -> dict | None:
    return call_sp_one(cursor, "sp_tedarikciler_getir", [tedarikci_id])


def tedarikci_ekle(cursor, ad, iletisim, borc) -> int:
    row = call_sp_one(cursor, "sp_tedarikciler_ekle", [ad, iletisim, borc])
    return row["id"] if row else None


def tedarikci_guncelle(cursor, tid, ad, iletisim, borc, silindi_mi) -> None:
    call_sp(cursor, "sp_tedarikciler_guncelle", [tid, ad, iletisim, borc, int(silindi_mi)])


def tedarikci_sil(cursor, tedarikci_id: int) -> None:
    call_sp(cursor, "sp_tedarikciler_sil", [tedarikci_id])


def kisiler_tedarikciye_gore(cursor, tedarikci_id: int) -> list:
    return call_sp(cursor, "sp_tedarikci_kisileri_tedarikciye_gore_listele", [tedarikci_id])


def kisi_ekle(cursor, tid, ad_soyad, gorevi, telefon, eposta, notlar) -> None:
    call_sp(cursor, "sp_tedarikci_kisileri_ekle", [tid, ad_soyad, gorevi, telefon, eposta, notlar])


def kisi_guncelle(cursor, kid, tid, ad_soyad, gorevi, telefon, eposta, notlar) -> None:
    call_sp(cursor, "sp_tedarikci_kisileri_guncelle", [kid, tid, ad_soyad, gorevi, telefon, eposta, notlar])


def kisi_sil(cursor, kisi_id: int) -> None:
    call_sp(cursor, "sp_tedarikci_kisileri_sil", [kisi_id])


def odemeler_tedarikciye_gore(cursor, tedarikci_id: int) -> list:
    return call_sp(cursor, "sp_tedarikci_odemeleri_tedarikciye_gore_listele", [tedarikci_id])


def odeme_ekle(cursor, tedarikci_id: int, tutar: float) -> int:
    row = call_sp_one(cursor, "sp_tedarikci_odemeleri_ekle", [tedarikci_id, tutar])
    return row["id"] if row else None


def odeme_sil(cursor, odeme_id: int) -> None:
    call_sp(cursor, "sp_tedarikci_odemeleri_sil", [odeme_id])

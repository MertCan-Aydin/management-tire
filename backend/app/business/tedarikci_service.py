from fastapi import HTTPException, status

from ..data_access import tedarikci_dal


def listele(cursor) -> list:
    return tedarikci_dal.tedarikciler_listele(cursor)


def getir(cursor, tid: int) -> dict:
    t = tedarikci_dal.tedarikci_getir(cursor, tid)
    if not t:
        raise HTTPException(status_code=404, detail="Tedarikçi bulunamadı")
    return t


def ekle(cursor, data) -> int:
    return tedarikci_dal.tedarikci_ekle(cursor, data.ad, data.iletisim_bilgisi, data.guncel_borc)


def guncelle(cursor, tid: int, data) -> None:
    getir(cursor, tid)
    tedarikci_dal.tedarikci_guncelle(cursor, tid, data.ad, data.iletisim_bilgisi, data.guncel_borc, data.silindi_mi)


def sil(cursor, tid: int) -> None:
    getir(cursor, tid)
    tedarikci_dal.tedarikci_sil(cursor, tid)


def kisiler_listele(cursor, tid: int) -> list:
    getir(cursor, tid)
    return tedarikci_dal.kisiler_tedarikciye_gore(cursor, tid)


def kisi_ekle(cursor, data) -> None:
    getir(cursor, data.tedarikci_id)
    tedarikci_dal.kisi_ekle(cursor, data.tedarikci_id, data.ad_soyad, data.gorevi, data.telefon, data.eposta, data.notlar)


def kisi_guncelle(cursor, kid: int, data) -> None:
    tedarikci_dal.kisi_guncelle(cursor, kid, data.tedarikci_id, data.ad_soyad, data.gorevi, data.telefon, data.eposta, data.notlar)


def kisi_sil(cursor, kid: int) -> None:
    tedarikci_dal.kisi_sil(cursor, kid)


def odemeler_listele(cursor, tid: int) -> list:
    getir(cursor, tid)
    return tedarikci_dal.odemeler_tedarikciye_gore(cursor, tid)


def odeme_ekle(cursor, data) -> int:
    getir(cursor, data.tedarikci_id)
    return tedarikci_dal.odeme_ekle(cursor, data.tedarikci_id, data.tutar)


def odeme_sil(cursor, odeme_id: int) -> None:
    tedarikci_dal.odeme_sil(cursor, odeme_id)

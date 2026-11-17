from ..core.db import call_sp, call_sp_one


# --- Ürün Tipleri ---

def urun_tipleri_listele(cursor) -> list:
    return call_sp(cursor, "sp_urun_tipleri_listele")


def urun_tipi_getir(cursor, tip_id: int) -> dict | None:
    return call_sp_one(cursor, "sp_urun_tipleri_getir", [tip_id])


def urun_tipi_ekle(cursor, ad: str) -> None:
    call_sp(cursor, "sp_urun_tipleri_ekle", [ad])


def urun_tipi_guncelle(cursor, tip_id: int, ad: str) -> None:
    call_sp(cursor, "sp_urun_tipleri_guncelle", [tip_id, ad])


def urun_tipi_sil(cursor, tip_id: int) -> None:
    call_sp(cursor, "sp_urun_tipleri_sil", [tip_id])


# --- Markalar ---

def markalar_listele(cursor) -> list:
    return call_sp(cursor, "sp_urun_markalari_listele")


def markalar_tipe_gore_listele(cursor, tip_id: int) -> list:
    return call_sp(cursor, "sp_urun_markalari_tipe_gore_listele", [tip_id])


def marka_getir(cursor, marka_id: int) -> dict | None:
    return call_sp_one(cursor, "sp_urun_markalari_getir", [marka_id])


def marka_ekle(cursor, tip_id: int, ad: str) -> None:
    call_sp(cursor, "sp_urun_markalari_ekle", [tip_id, ad])


def marka_guncelle(cursor, marka_id: int, tip_id: int, ad: str) -> None:
    call_sp(cursor, "sp_urun_markalari_guncelle", [marka_id, tip_id, ad])


def marka_sil(cursor, marka_id: int) -> None:
    call_sp(cursor, "sp_urun_markalari_sil", [marka_id])


# --- Modeller ---

def modeller_listele(cursor) -> list:
    return call_sp(cursor, "sp_urun_marka_modelleri_listele")


def modeller_markaya_gore_listele(cursor, marka_id: int) -> list:
    return call_sp(cursor, "sp_urun_marka_modelleri_markaya_gore_listele", [marka_id])


def model_getir(cursor, model_id: int) -> dict | None:
    return call_sp_one(cursor, "sp_urun_marka_modelleri_getir", [model_id])


def model_ekle(cursor, marka_id: int, ad: str, mevsim: str | None) -> None:
    call_sp(cursor, "sp_urun_marka_modelleri_ekle", [marka_id, ad, mevsim])


def model_guncelle(cursor, model_id: int, marka_id: int, ad: str, mevsim: str | None) -> None:
    call_sp(cursor, "sp_urun_marka_modelleri_guncelle", [model_id, marka_id, ad, mevsim])


def model_sil(cursor, model_id: int) -> None:
    call_sp(cursor, "sp_urun_marka_modelleri_sil", [model_id])


# --- Ürünler ---

def urunler_listele(cursor, arama, tip_id, marka_id, sadece_stoklu, limit, offset) -> list:
    return call_sp(cursor, "sp_urunler_listele", [arama, tip_id, marka_id, int(sadece_stoklu), limit, offset])


def urun_getir(cursor, urun_id: int) -> dict | None:
    return call_sp_one(cursor, "sp_urunler_getir", [urun_id])


def urun_barkod_ara(cursor, barkod: str) -> dict | None:
    return call_sp_one(cursor, "sp_urunler_barkod_ara", [barkod])


def urun_ekle(cursor, data: dict) -> int:
    row = call_sp_one(cursor, "sp_urunler_ekle", [
        data["barkod_qr"], data["ad"], data["ebat"],
        data.get("yuk_indeksi"), data.get("hiz_kodu"),
        int(data.get("ekstra_yuk", False)), data.get("uretim_yili"),
        data["aciklama"],
        data["satis_fiyati"], data["maliyet_fiyati"],
        int(data.get("maliyet_bilinmiyor", False)),
        int(data.get("guncel_borctan", False)),
        data["stok"],
        int(data["fiziksel_urun_mu"]), data["resim_yolu"],
        data["urun_tipi_id"], data["marka_id"], data["marka_modeli_id"],
    ])
    return row["id"] if row else None


def urun_guncelle(cursor, urun_id: int, data: dict) -> None:
    call_sp(cursor, "sp_urunler_guncelle", [
        urun_id,
        data["barkod_qr"], data["ad"], data["ebat"],
        data.get("yuk_indeksi"), data.get("hiz_kodu"),
        int(data.get("ekstra_yuk", False)), data.get("uretim_yili"),
        data["aciklama"],
        data["satis_fiyati"], data["maliyet_fiyati"],
        int(data.get("maliyet_bilinmiyor", False)),
        int(data.get("guncel_borctan", False)),
        data["stok"],
        int(data["fiziksel_urun_mu"]), data["resim_yolu"], int(data["silindi_mi"]),
        data["urun_tipi_id"], data["marka_id"], data["marka_modeli_id"],
    ])


def urun_sil(cursor, urun_id: int) -> None:
    call_sp(cursor, "sp_urunler_sil", [urun_id])


# --- EPREL entegrasyonu ---

def urun_tipi_bul_veya_olustur(cursor, ad: str) -> int:
    row = call_sp_one(cursor, "sp_urun_tipi_bul_veya_olustur", [ad])
    return row["id"]


def urun_markasi_bul_veya_olustur(cursor, tipi_id: int, ad: str) -> int:
    row = call_sp_one(cursor, "sp_urun_markasi_bul_veya_olustur", [tipi_id, ad])
    return row["id"]


def urun_modeli_bul_veya_olustur(cursor, marka_id: int, ad: str, mevsim: str) -> int:
    row = call_sp_one(cursor, "sp_urun_modeli_bul_veya_olustur", [marka_id, ad, mevsim])
    return row["id"]


def urun_eprel_bul(cursor, eprel_no: str) -> dict | None:
    return call_sp_one(cursor, "sp_urun_eprel_bul", [eprel_no])


def urun_eprel_bul_silinmis(cursor, eprel_no: str) -> dict | None:
    cursor.execute(
        "SELECT id, ad, satis_fiyati, maliyet_fiyati, barkod_qr FROM urunler WHERE barkod_qr = %s AND silindi_mi = 1 LIMIT 1",
        [eprel_no],
    )
    return cursor.fetchone()


def urun_geri_aktiflestir(cursor, urun_id: int) -> None:
    cursor.execute("UPDATE urunler SET silindi_mi = 0 WHERE id = %s", [urun_id])


def urun_ad_ile_bul(cursor, marka: str, model: str, ebat: str,
                     yuk_indeksi: str | None = None, hiz_kodu: str | None = None,
                     ekstra_yuk: bool = False, uretim_yili: int | None = None) -> dict | None:
    return call_sp_one(cursor, "sp_urun_tam_eslesme_bul", [
        marka, model, ebat, yuk_indeksi, hiz_kodu, int(ekstra_yuk), uretim_yili,
    ])


def urun_barkod_guncelle(cursor, urun_id: int, yeni_barkod: str) -> None:
    cursor.execute("UPDATE urunler SET barkod_qr = %s WHERE id = %s", [yeni_barkod, urun_id])

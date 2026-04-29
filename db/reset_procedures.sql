-- =============================================
-- MEVCUT SP / FONKSİYON / TRIGGER TEMİZLEME
-- Orijinal Script-12.sql'den gelen nesneleri temizler.
-- Bu scriptten SONRA 002-006 migration dosyalarını uygula.
-- =============================================

USE DijitalLastikServisiDB;

-- Trigger'lar
DROP TRIGGER IF EXISTS trg_satis_kalemi_eklendikten_sonra;
DROP TRIGGER IF EXISTS trg_alim_kalemi_eklendikten_sonra;
DROP TRIGGER IF EXISTS trg_tedarikciye_odeme_yapildiginda;

-- Fonksiyonlar
DROP FUNCTION IF EXISTS fn_urun_stok_durumu;
DROP FUNCTION IF EXISTS fn_satis_kari_hesapla;

-- Stored Procedure'ler (orijinal + yeni)
DROP PROCEDURE IF EXISTS sp_urun_tipleri_ekle;
DROP PROCEDURE IF EXISTS sp_urun_tipleri_guncelle;
DROP PROCEDURE IF EXISTS sp_urun_tipleri_sil;
DROP PROCEDURE IF EXISTS sp_urun_tipleri_listele;
DROP PROCEDURE IF EXISTS sp_urun_tipleri_getir;

DROP PROCEDURE IF EXISTS sp_urun_markalari_ekle;
DROP PROCEDURE IF EXISTS sp_urun_markalari_guncelle;
DROP PROCEDURE IF EXISTS sp_urun_markalari_sil;
DROP PROCEDURE IF EXISTS sp_urun_markalari_listele;
DROP PROCEDURE IF EXISTS sp_urun_markalari_getir;
DROP PROCEDURE IF EXISTS sp_urun_markalari_tipe_gore_listele;

DROP PROCEDURE IF EXISTS sp_urun_marka_modelleri_ekle;
DROP PROCEDURE IF EXISTS sp_urun_marka_modelleri_guncelle;
DROP PROCEDURE IF EXISTS sp_urun_marka_modelleri_sil;
DROP PROCEDURE IF EXISTS sp_urun_marka_modelleri_listele;
DROP PROCEDURE IF EXISTS sp_urun_marka_modelleri_getir;
DROP PROCEDURE IF EXISTS sp_urun_marka_modelleri_markaya_gore_listele;

DROP PROCEDURE IF EXISTS sp_urunler_ekle;
DROP PROCEDURE IF EXISTS sp_urunler_guncelle;
DROP PROCEDURE IF EXISTS sp_urunler_sil;
DROP PROCEDURE IF EXISTS sp_urunler_listele;
DROP PROCEDURE IF EXISTS sp_urunler_getir;
DROP PROCEDURE IF EXISTS sp_urunler_barkod_ara;

DROP PROCEDURE IF EXISTS sp_urun_partileri_ekle;
DROP PROCEDURE IF EXISTS sp_urun_partileri_guncelle;
DROP PROCEDURE IF EXISTS sp_urun_partileri_sil;
DROP PROCEDURE IF EXISTS sp_urun_partileri_listele;
DROP PROCEDURE IF EXISTS sp_urun_partileri_urune_gore_listele;

DROP PROCEDURE IF EXISTS sp_tedarikciler_ekle;
DROP PROCEDURE IF EXISTS sp_tedarikciler_guncelle;
DROP PROCEDURE IF EXISTS sp_tedarikciler_sil;
DROP PROCEDURE IF EXISTS sp_tedarikciler_listele;
DROP PROCEDURE IF EXISTS sp_tedarikciler_getir;

DROP PROCEDURE IF EXISTS sp_tedarikci_kisileri_ekle;
DROP PROCEDURE IF EXISTS sp_tedarikci_kisileri_guncelle;
DROP PROCEDURE IF EXISTS sp_tedarikci_kisileri_sil;
DROP PROCEDURE IF EXISTS sp_tedarikci_kisileri_listele;
DROP PROCEDURE IF EXISTS sp_tedarikci_kisileri_tedarikciye_gore_listele;

DROP PROCEDURE IF EXISTS sp_tedarikci_odemeleri_ekle;
DROP PROCEDURE IF EXISTS sp_tedarikci_odemeleri_guncelle;
DROP PROCEDURE IF EXISTS sp_tedarikci_odemeleri_sil;
DROP PROCEDURE IF EXISTS sp_tedarikci_odemeleri_listele;
DROP PROCEDURE IF EXISTS sp_tedarikci_odemeleri_tedarikciye_gore_listele;

DROP PROCEDURE IF EXISTS sp_alimlar_ekle;
DROP PROCEDURE IF EXISTS sp_alimlar_guncelle;
DROP PROCEDURE IF EXISTS sp_alimlar_sil;
DROP PROCEDURE IF EXISTS sp_alimlar_listele;
DROP PROCEDURE IF EXISTS sp_alimlar_getir;

DROP PROCEDURE IF EXISTS sp_alim_kalemleri_ekle;
DROP PROCEDURE IF EXISTS sp_alim_kalemleri_guncelle;
DROP PROCEDURE IF EXISTS sp_alim_kalemleri_sil;
DROP PROCEDURE IF EXISTS sp_alim_kalemleri_listele;
DROP PROCEDURE IF EXISTS sp_alim_kalemleri_alima_gore_listele;

DROP PROCEDURE IF EXISTS sp_musteriler_ekle;
DROP PROCEDURE IF EXISTS sp_musteriler_guncelle;
DROP PROCEDURE IF EXISTS sp_musteriler_sil;
DROP PROCEDURE IF EXISTS sp_musteriler_listele;
DROP PROCEDURE IF EXISTS sp_musteriler_getir;
DROP PROCEDURE IF EXISTS sp_musteriler_plaka_ara;
DROP PROCEDURE IF EXISTS sp_musteriler_telefon_ara;

DROP PROCEDURE IF EXISTS sp_satislar_ekle;
DROP PROCEDURE IF EXISTS sp_satislar_guncelle;
DROP PROCEDURE IF EXISTS sp_satislar_sil;
DROP PROCEDURE IF EXISTS sp_satislar_listele;
DROP PROCEDURE IF EXISTS sp_satislar_getir;

DROP PROCEDURE IF EXISTS sp_satis_kalemleri_ekle;
DROP PROCEDURE IF EXISTS sp_satis_kalemleri_guncelle;
DROP PROCEDURE IF EXISTS sp_satis_kalemleri_sil;
DROP PROCEDURE IF EXISTS sp_satis_kalemleri_listele;
DROP PROCEDURE IF EXISTS sp_satis_kalemleri_satisa_gore_listele;

DROP PROCEDURE IF EXISTS sp_giderler_ekle;
DROP PROCEDURE IF EXISTS sp_giderler_guncelle;
DROP PROCEDURE IF EXISTS sp_giderler_sil;
DROP PROCEDURE IF EXISTS sp_giderler_listele;
DROP PROCEDURE IF EXISTS sp_giderler_getir;

DROP PROCEDURE IF EXISTS sp_iptal_kayitlari_ekle;
DROP PROCEDURE IF EXISTS sp_iptal_kayitlari_guncelle;
DROP PROCEDURE IF EXISTS sp_iptal_kayitlari_sil;
DROP PROCEDURE IF EXISTS sp_iptal_kayitlari_listele;

-- Auth (yeni)
DROP PROCEDURE IF EXISTS sp_kullanici_olustur;
DROP PROCEDURE IF EXISTS sp_kullanici_adi_ile_getir;
DROP PROCEDURE IF EXISTS sp_kullanici_getir;
DROP PROCEDURE IF EXISTS sp_kullanici_giris_tarihi_guncelle;
DROP PROCEDURE IF EXISTS sp_kullanici_parola_guncelle;
DROP PROCEDURE IF EXISTS sp_refresh_token_ekle;
DROP PROCEDURE IF EXISTS sp_refresh_token_getir;
DROP PROCEDURE IF EXISTS sp_refresh_token_iptal;
DROP PROCEDURE IF EXISTS sp_refresh_tokenlari_kullaniciya_gore_iptal;
DROP PROCEDURE IF EXISTS sp_suresi_gecmis_tokenlari_temizle;

-- Rapor (yeni)
DROP PROCEDURE IF EXISTS sp_rapor_gunluk;
DROP PROCEDURE IF EXISTS sp_rapor_aralik;
DROP PROCEDURE IF EXISTS sp_rapor_gunluk_kirilim;
DROP PROCEDURE IF EXISTS sp_rapor_en_cok_satan;
DROP PROCEDURE IF EXISTS sp_dashboard_ozet;
DROP PROCEDURE IF EXISTS sp_rapor_tedarikci_alim;

SELECT 'Temizleme tamamlandı — şimdi migration dosyalarını uygulayabilirsiniz.' AS Sonuc;

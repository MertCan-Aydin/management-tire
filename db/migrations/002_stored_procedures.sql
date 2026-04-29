-- =============================================
-- 002 — STORED PROCEDURE'LER
-- =============================================

USE DijitalLastikServisiDB;

-- ###############################################
-- urun_tipleri
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_urun_tipleri_ekle(IN p_ad VARCHAR(50))
BEGIN
    INSERT INTO urun_tipleri (ad) VALUES (p_ad);
END //

CREATE PROCEDURE sp_urun_tipleri_guncelle(IN p_id INT, IN p_ad VARCHAR(50))
BEGIN
    UPDATE urun_tipleri SET ad = p_ad WHERE id = p_id;
END //

CREATE PROCEDURE sp_urun_tipleri_sil(IN p_id INT)
BEGIN
    DELETE FROM urun_tipleri WHERE id = p_id;
END //

CREATE PROCEDURE sp_urun_tipleri_listele()
BEGIN
    SELECT id, ad FROM urun_tipleri ORDER BY ad;
END //

CREATE PROCEDURE sp_urun_tipleri_getir(IN p_id INT)
BEGIN
    SELECT id, ad FROM urun_tipleri WHERE id = p_id;
END //

DELIMITER ;

-- ###############################################
-- urun_markalari
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_urun_markalari_ekle(IN p_urun_tipi_id INT, IN p_ad VARCHAR(50))
BEGIN
    INSERT INTO urun_markalari (urun_tipi_id, ad) VALUES (p_urun_tipi_id, p_ad);
END //

CREATE PROCEDURE sp_urun_markalari_guncelle(IN p_id INT, IN p_urun_tipi_id INT, IN p_ad VARCHAR(50))
BEGIN
    UPDATE urun_markalari SET urun_tipi_id = p_urun_tipi_id, ad = p_ad WHERE id = p_id;
END //

CREATE PROCEDURE sp_urun_markalari_sil(IN p_id INT)
BEGIN
    DELETE FROM urun_markalari WHERE id = p_id;
END //

CREATE PROCEDURE sp_urun_markalari_listele()
BEGIN
    SELECT id, urun_tipi_id, ad FROM urun_markalari ORDER BY ad;
END //

CREATE PROCEDURE sp_urun_markalari_getir(IN p_id INT)
BEGIN
    SELECT id, urun_tipi_id, ad FROM urun_markalari WHERE id = p_id;
END //

CREATE PROCEDURE sp_urun_markalari_tipe_gore_listele(IN p_urun_tipi_id INT)
BEGIN
    SELECT id, urun_tipi_id, ad FROM urun_markalari WHERE urun_tipi_id = p_urun_tipi_id ORDER BY ad;
END //

DELIMITER ;

-- ###############################################
-- urun_marka_modelleri
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_urun_marka_modelleri_ekle(IN p_marka_id INT, IN p_ad VARCHAR(50), IN p_mevsim VARCHAR(20))
BEGIN
    INSERT INTO urun_marka_modelleri (marka_id, ad, mevsim) VALUES (p_marka_id, p_ad, p_mevsim);
END //

CREATE PROCEDURE sp_urun_marka_modelleri_guncelle(IN p_id INT, IN p_marka_id INT, IN p_ad VARCHAR(50), IN p_mevsim VARCHAR(20))
BEGIN
    UPDATE urun_marka_modelleri SET marka_id = p_marka_id, ad = p_ad, mevsim = p_mevsim WHERE id = p_id;
END //

CREATE PROCEDURE sp_urun_marka_modelleri_sil(IN p_id INT)
BEGIN
    DELETE FROM urun_marka_modelleri WHERE id = p_id;
END //

CREATE PROCEDURE sp_urun_marka_modelleri_listele()
BEGIN
    SELECT id, marka_id, ad, mevsim FROM urun_marka_modelleri ORDER BY ad;
END //

CREATE PROCEDURE sp_urun_marka_modelleri_getir(IN p_id INT)
BEGIN
    SELECT id, marka_id, ad, mevsim FROM urun_marka_modelleri WHERE id = p_id;
END //

CREATE PROCEDURE sp_urun_marka_modelleri_markaya_gore_listele(IN p_marka_id INT)
BEGIN
    SELECT id, marka_id, ad, mevsim FROM urun_marka_modelleri WHERE marka_id = p_marka_id ORDER BY ad;
END //

DELIMITER ;

-- ###############################################
-- urunler
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_urunler_ekle(
    IN p_barkod_qr VARCHAR(100),
    IN p_ad VARCHAR(100),
    IN p_ebat VARCHAR(50),
    IN p_aciklama TEXT,
    IN p_satis_fiyati DECIMAL(18,2),
    IN p_maliyet_fiyati DECIMAL(18,2),
    IN p_stok INT,
    IN p_fiziksel_urun_mu BOOLEAN,
    IN p_resim_yolu VARCHAR(255),
    IN p_urun_tipi_id INT,
    IN p_marka_id INT,
    IN p_marka_modeli_id INT
)
BEGIN
    INSERT INTO urunler (
        barkod_qr, ad, ebat, aciklama, satis_fiyati,
        maliyet_fiyati, stok, fiziksel_urun_mu, resim_yolu,
        urun_tipi_id, marka_id, marka_modeli_id
    ) VALUES (
        p_barkod_qr, p_ad, p_ebat, p_aciklama, p_satis_fiyati,
        p_maliyet_fiyati, p_stok, p_fiziksel_urun_mu, p_resim_yolu,
        p_urun_tipi_id, p_marka_id, p_marka_modeli_id
    );
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_urunler_guncelle(
    IN p_id INT,
    IN p_barkod_qr VARCHAR(100),
    IN p_ad VARCHAR(100),
    IN p_ebat VARCHAR(50),
    IN p_aciklama TEXT,
    IN p_satis_fiyati DECIMAL(18,2),
    IN p_maliyet_fiyati DECIMAL(18,2),
    IN p_stok INT,
    IN p_fiziksel_urun_mu BOOLEAN,
    IN p_resim_yolu VARCHAR(255),
    IN p_silindi_mi BOOLEAN,
    IN p_urun_tipi_id INT,
    IN p_marka_id INT,
    IN p_marka_modeli_id INT
)
BEGIN
    UPDATE urunler SET
        barkod_qr = p_barkod_qr,
        ad = p_ad,
        ebat = p_ebat,
        aciklama = p_aciklama,
        satis_fiyati = p_satis_fiyati,
        maliyet_fiyati = p_maliyet_fiyati,
        stok = p_stok,
        fiziksel_urun_mu = p_fiziksel_urun_mu,
        resim_yolu = p_resim_yolu,
        silindi_mi = p_silindi_mi,
        urun_tipi_id = p_urun_tipi_id,
        marka_id = p_marka_id,
        marka_modeli_id = p_marka_modeli_id
    WHERE id = p_id;
END //

CREATE PROCEDURE sp_urunler_sil(IN p_id INT)
BEGIN
    -- Soft delete
    UPDATE urunler SET silindi_mi = 1 WHERE id = p_id;
END //

CREATE PROCEDURE sp_urunler_listele(
    IN p_arama VARCHAR(100),
    IN p_urun_tipi_id INT,
    IN p_marka_id INT,
    IN p_sadece_stoklu BOOLEAN,
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    SELECT
        u.id, u.barkod_qr, u.ad, u.ebat, u.satis_fiyati,
        u.maliyet_fiyati, u.stok, u.fiziksel_urun_mu,
        u.resim_yolu, u.silindi_mi,
        u.urun_tipi_id, u.marka_id, u.marka_modeli_id,
        t.ad AS tip_adi, m.ad AS marka_adi, mm.ad AS model_adi, mm.mevsim
    FROM urunler u
    JOIN urun_tipleri t ON t.id = u.urun_tipi_id
    JOIN urun_markalari m ON m.id = u.marka_id
    JOIN urun_marka_modelleri mm ON mm.id = u.marka_modeli_id
    WHERE
        u.silindi_mi = 0
        AND (p_arama IS NULL OR u.ad LIKE CONCAT('%', p_arama, '%') OR u.barkod_qr = p_arama OR u.ebat LIKE CONCAT('%', p_arama, '%'))
        AND (p_urun_tipi_id IS NULL OR u.urun_tipi_id = p_urun_tipi_id)
        AND (p_marka_id IS NULL OR u.marka_id = p_marka_id)
        AND (p_sadece_stoklu = 0 OR u.stok > 0)
    ORDER BY u.ad
    LIMIT p_limit OFFSET p_offset;
END //

CREATE PROCEDURE sp_urunler_getir(IN p_id INT)
BEGIN
    SELECT
        u.id, u.barkod_qr, u.ad, u.ebat, u.aciklama,
        u.satis_fiyati, u.maliyet_fiyati, u.stok, u.fiziksel_urun_mu,
        u.resim_yolu, u.silindi_mi,
        u.urun_tipi_id, u.marka_id, u.marka_modeli_id,
        t.ad AS tip_adi, m.ad AS marka_adi, mm.ad AS model_adi, mm.mevsim
    FROM urunler u
    JOIN urun_tipleri t ON t.id = u.urun_tipi_id
    JOIN urun_markalari m ON m.id = u.marka_id
    JOIN urun_marka_modelleri mm ON mm.id = u.marka_modeli_id
    WHERE u.id = p_id;
END //

CREATE PROCEDURE sp_urunler_barkod_ara(IN p_barkod VARCHAR(100))
BEGIN
    SELECT
        u.id, u.barkod_qr, u.ad, u.ebat,
        u.satis_fiyati, u.maliyet_fiyati, u.stok, u.fiziksel_urun_mu,
        u.urun_tipi_id, u.marka_id, u.marka_modeli_id,
        t.ad AS tip_adi, m.ad AS marka_adi, mm.ad AS model_adi, mm.mevsim
    FROM urunler u
    JOIN urun_tipleri t ON t.id = u.urun_tipi_id
    JOIN urun_markalari m ON m.id = u.marka_id
    JOIN urun_marka_modelleri mm ON mm.id = u.marka_modeli_id
    WHERE u.barkod_qr = p_barkod AND u.silindi_mi = 0;
END //

DELIMITER ;

-- ###############################################
-- urun_partileri
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_urun_partileri_ekle(IN p_urun_id INT, IN p_miktar INT, IN p_birim_maliyet DECIMAL(18,2))
BEGIN
    INSERT INTO urun_partileri (urun_id, miktar, birim_maliyet) VALUES (p_urun_id, p_miktar, p_birim_maliyet);
END //

CREATE PROCEDURE sp_urun_partileri_guncelle(IN p_id INT, IN p_urun_id INT, IN p_miktar INT, IN p_birim_maliyet DECIMAL(18,2), IN p_eklenme_tarihi DATETIME)
BEGIN
    UPDATE urun_partileri SET urun_id = p_urun_id, miktar = p_miktar, birim_maliyet = p_birim_maliyet, eklenme_tarihi = p_eklenme_tarihi WHERE id = p_id;
END //

CREATE PROCEDURE sp_urun_partileri_sil(IN p_id INT)
BEGIN
    DELETE FROM urun_partileri WHERE id = p_id;
END //

CREATE PROCEDURE sp_urun_partileri_listele()
BEGIN
    SELECT id, urun_id, miktar, birim_maliyet, eklenme_tarihi FROM urun_partileri ORDER BY eklenme_tarihi DESC;
END //

CREATE PROCEDURE sp_urun_partileri_urune_gore_listele(IN p_urun_id INT)
BEGIN
    SELECT id, urun_id, miktar, birim_maliyet, eklenme_tarihi FROM urun_partileri WHERE urun_id = p_urun_id ORDER BY eklenme_tarihi DESC;
END //

DELIMITER ;

-- ###############################################
-- tedarikciler
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_tedarikciler_ekle(IN p_ad VARCHAR(100), IN p_iletisim_bilgisi VARCHAR(255), IN p_guncel_borc DECIMAL(18,2))
BEGIN
    INSERT INTO tedarikciler (ad, iletisim_bilgisi, guncel_borc) VALUES (p_ad, p_iletisim_bilgisi, p_guncel_borc);
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_tedarikciler_guncelle(IN p_id INT, IN p_ad VARCHAR(100), IN p_iletisim_bilgisi VARCHAR(255), IN p_guncel_borc DECIMAL(18,2), IN p_silindi_mi BOOLEAN)
BEGIN
    UPDATE tedarikciler SET ad = p_ad, iletisim_bilgisi = p_iletisim_bilgisi, guncel_borc = p_guncel_borc, silindi_mi = p_silindi_mi WHERE id = p_id;
END //

CREATE PROCEDURE sp_tedarikciler_sil(IN p_id INT)
BEGIN
    UPDATE tedarikciler SET silindi_mi = 1 WHERE id = p_id;
END //

CREATE PROCEDURE sp_tedarikciler_listele()
BEGIN
    SELECT id, ad, iletisim_bilgisi, guncel_borc, silindi_mi FROM tedarikciler WHERE silindi_mi = 0 ORDER BY ad;
END //

CREATE PROCEDURE sp_tedarikciler_getir(IN p_id INT)
BEGIN
    SELECT id, ad, iletisim_bilgisi, guncel_borc, silindi_mi FROM tedarikciler WHERE id = p_id;
END //

DELIMITER ;

-- ###############################################
-- tedarikci_kisileri
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_tedarikci_kisileri_ekle(IN p_tedarikci_id INT, IN p_ad_soyad VARCHAR(100), IN p_gorevi VARCHAR(50), IN p_telefon VARCHAR(20), IN p_eposta VARCHAR(100), IN p_notlar TEXT)
BEGIN
    INSERT INTO tedarikci_kisileri (tedarikci_id, ad_soyad, gorevi, telefon, eposta, notlar) VALUES (p_tedarikci_id, p_ad_soyad, p_gorevi, p_telefon, p_eposta, p_notlar);
END //

CREATE PROCEDURE sp_tedarikci_kisileri_guncelle(IN p_id INT, IN p_tedarikci_id INT, IN p_ad_soyad VARCHAR(100), IN p_gorevi VARCHAR(50), IN p_telefon VARCHAR(20), IN p_eposta VARCHAR(100), IN p_notlar TEXT)
BEGIN
    UPDATE tedarikci_kisileri SET tedarikci_id = p_tedarikci_id, ad_soyad = p_ad_soyad, gorevi = p_gorevi, telefon = p_telefon, eposta = p_eposta, notlar = p_notlar WHERE id = p_id;
END //

CREATE PROCEDURE sp_tedarikci_kisileri_sil(IN p_id INT)
BEGIN
    DELETE FROM tedarikci_kisileri WHERE id = p_id;
END //

CREATE PROCEDURE sp_tedarikci_kisileri_listele()
BEGIN
    SELECT id, tedarikci_id, ad_soyad, gorevi, telefon, eposta, notlar FROM tedarikci_kisileri;
END //

CREATE PROCEDURE sp_tedarikci_kisileri_tedarikciye_gore_listele(IN p_tedarikci_id INT)
BEGIN
    SELECT id, tedarikci_id, ad_soyad, gorevi, telefon, eposta, notlar FROM tedarikci_kisileri WHERE tedarikci_id = p_tedarikci_id;
END //

DELIMITER ;

-- ###############################################
-- tedarikci_odemeleri
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_tedarikci_odemeleri_ekle(IN p_tedarikci_id INT, IN p_tutar DECIMAL(18,2))
BEGIN
    INSERT INTO tedarikci_odemeleri (tedarikci_id, tutar) VALUES (p_tedarikci_id, p_tutar);
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_tedarikci_odemeleri_guncelle(IN p_id INT, IN p_tedarikci_id INT, IN p_tutar DECIMAL(18,2), IN p_tarih DATETIME)
BEGIN
    UPDATE tedarikci_odemeleri SET tedarikci_id = p_tedarikci_id, tutar = p_tutar, tarih = p_tarih WHERE id = p_id;
END //

CREATE PROCEDURE sp_tedarikci_odemeleri_sil(IN p_id INT)
BEGIN
    DELETE FROM tedarikci_odemeleri WHERE id = p_id;
END //

CREATE PROCEDURE sp_tedarikci_odemeleri_listele()
BEGIN
    SELECT id, tedarikci_id, tutar, tarih FROM tedarikci_odemeleri ORDER BY tarih DESC;
END //

CREATE PROCEDURE sp_tedarikci_odemeleri_tedarikciye_gore_listele(IN p_tedarikci_id INT)
BEGIN
    SELECT id, tedarikci_id, tutar, tarih FROM tedarikci_odemeleri WHERE tedarikci_id = p_tedarikci_id ORDER BY tarih DESC;
END //

DELIMITER ;

-- ###############################################
-- alimlar
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_alimlar_ekle(IN p_tedarikci_id INT, IN p_toplam_tutar DECIMAL(18,2))
BEGIN
    INSERT INTO alimlar (tedarikci_id, toplam_tutar) VALUES (p_tedarikci_id, p_toplam_tutar);
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_alimlar_guncelle(IN p_id INT, IN p_tedarikci_id INT, IN p_toplam_tutar DECIMAL(18,2), IN p_tarih DATETIME, IN p_iptal_mi BOOLEAN)
BEGIN
    UPDATE alimlar SET tedarikci_id = p_tedarikci_id, toplam_tutar = p_toplam_tutar, tarih = p_tarih, iptal_mi = p_iptal_mi WHERE id = p_id;
END //

CREATE PROCEDURE sp_alimlar_sil(IN p_id INT)
BEGIN
    DELETE FROM alimlar WHERE id = p_id;
END //

CREATE PROCEDURE sp_alimlar_listele(IN p_baslangic_tarihi DATETIME, IN p_bitis_tarihi DATETIME, IN p_tedarikci_id INT, IN p_limit INT, IN p_offset INT)
BEGIN
    SELECT
        a.id, a.tarih, a.toplam_tutar, a.tedarikci_id, a.iptal_mi,
        t.ad AS tedarikci_adi
    FROM alimlar a
    JOIN tedarikciler t ON t.id = a.tedarikci_id
    WHERE
        (p_baslangic_tarihi IS NULL OR a.tarih >= p_baslangic_tarihi)
        AND (p_bitis_tarihi IS NULL OR a.tarih <= p_bitis_tarihi)
        AND (p_tedarikci_id IS NULL OR a.tedarikci_id = p_tedarikci_id)
    ORDER BY a.tarih DESC
    LIMIT p_limit OFFSET p_offset;
END //

CREATE PROCEDURE sp_alimlar_getir(IN p_id INT)
BEGIN
    SELECT a.id, a.tarih, a.toplam_tutar, a.tedarikci_id, a.iptal_mi, t.ad AS tedarikci_adi
    FROM alimlar a JOIN tedarikciler t ON t.id = a.tedarikci_id
    WHERE a.id = p_id;
END //

DELIMITER ;

-- ###############################################
-- alim_kalemleri
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_alim_kalemleri_ekle(IN p_alim_id INT, IN p_urun_id INT, IN p_urun_adi_anlik VARCHAR(100), IN p_miktar INT, IN p_birim_fiyat DECIMAL(18,2))
BEGIN
    INSERT INTO alim_kalemleri (alim_id, urun_id, urun_adi_anlik, miktar, birim_fiyat) VALUES (p_alim_id, p_urun_id, p_urun_adi_anlik, p_miktar, p_birim_fiyat);
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_alim_kalemleri_guncelle(IN p_id INT, IN p_alim_id INT, IN p_urun_id INT, IN p_urun_adi_anlik VARCHAR(100), IN p_miktar INT, IN p_birim_fiyat DECIMAL(18,2))
BEGIN
    UPDATE alim_kalemleri SET alim_id = p_alim_id, urun_id = p_urun_id, urun_adi_anlik = p_urun_adi_anlik, miktar = p_miktar, birim_fiyat = p_birim_fiyat WHERE id = p_id;
END //

CREATE PROCEDURE sp_alim_kalemleri_sil(IN p_id INT)
BEGIN
    DELETE FROM alim_kalemleri WHERE id = p_id;
END //

CREATE PROCEDURE sp_alim_kalemleri_alima_gore_listele(IN p_alim_id INT)
BEGIN
    SELECT ak.id, ak.alim_id, ak.urun_id, ak.urun_adi_anlik, ak.miktar, ak.birim_fiyat,
           (ak.miktar * ak.birim_fiyat) AS toplam_fiyat
    FROM alim_kalemleri ak
    WHERE ak.alim_id = p_alim_id;
END //

DELIMITER ;

-- ###############################################
-- musteriler
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_musteriler_ekle(IN p_ad_soyad VARCHAR(100), IN p_telefon VARCHAR(20), IN p_arac_markasi VARCHAR(50), IN p_arac_plakasi VARCHAR(20), IN p_notlar TEXT)
BEGIN
    INSERT INTO musteriler (ad_soyad, telefon, arac_markasi, arac_plakasi, notlar) VALUES (p_ad_soyad, p_telefon, p_arac_markasi, p_arac_plakasi, p_notlar);
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_musteriler_guncelle(IN p_id INT, IN p_ad_soyad VARCHAR(100), IN p_telefon VARCHAR(20), IN p_arac_markasi VARCHAR(50), IN p_arac_plakasi VARCHAR(20), IN p_notlar TEXT)
BEGIN
    UPDATE musteriler SET ad_soyad = p_ad_soyad, telefon = p_telefon, arac_markasi = p_arac_markasi, arac_plakasi = p_arac_plakasi, notlar = p_notlar WHERE id = p_id;
END //

CREATE PROCEDURE sp_musteriler_sil(IN p_id INT)
BEGIN
    DELETE FROM musteriler WHERE id = p_id;
END //

CREATE PROCEDURE sp_musteriler_listele(IN p_arama VARCHAR(100), IN p_limit INT, IN p_offset INT)
BEGIN
    SELECT id, ad_soyad, telefon, arac_markasi, arac_plakasi, notlar
    FROM musteriler
    WHERE (p_arama IS NULL OR ad_soyad LIKE CONCAT('%', p_arama, '%') OR telefon LIKE CONCAT('%', p_arama, '%') OR arac_plakasi LIKE CONCAT('%', p_arama, '%'))
    ORDER BY ad_soyad
    LIMIT p_limit OFFSET p_offset;
END //

CREATE PROCEDURE sp_musteriler_getir(IN p_id INT)
BEGIN
    SELECT id, ad_soyad, telefon, arac_markasi, arac_plakasi, notlar FROM musteriler WHERE id = p_id;
END //

CREATE PROCEDURE sp_musteriler_plaka_ara(IN p_plaka VARCHAR(20))
BEGIN
    SELECT id, ad_soyad, telefon, arac_markasi, arac_plakasi, notlar FROM musteriler WHERE arac_plakasi = p_plaka;
END //

CREATE PROCEDURE sp_musteriler_telefon_ara(IN p_telefon VARCHAR(20))
BEGIN
    SELECT id, ad_soyad, telefon, arac_markasi, arac_plakasi, notlar FROM musteriler WHERE telefon = p_telefon;
END //

DELIMITER ;

-- ###############################################
-- satislar
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_satislar_ekle(IN p_musteri_id INT, IN p_odeme_yontemi VARCHAR(50), IN p_toplam_tutar DECIMAL(18,2), IN p_toplam_maliyet DECIMAL(18,2), IN p_indirim DECIMAL(18,2))
BEGIN
    INSERT INTO satislar (musteri_id, odeme_yontemi, toplam_tutar, toplam_maliyet, indirim) VALUES (p_musteri_id, p_odeme_yontemi, p_toplam_tutar, p_toplam_maliyet, p_indirim);
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_satislar_guncelle(IN p_id INT, IN p_musteri_id INT, IN p_odeme_yontemi VARCHAR(50), IN p_toplam_tutar DECIMAL(18,2), IN p_toplam_maliyet DECIMAL(18,2), IN p_indirim DECIMAL(18,2), IN p_tarih DATETIME, IN p_iptal_mi BOOLEAN)
BEGIN
    UPDATE satislar SET musteri_id = p_musteri_id, odeme_yontemi = p_odeme_yontemi, toplam_tutar = p_toplam_tutar, toplam_maliyet = p_toplam_maliyet, indirim = p_indirim, tarih = p_tarih, iptal_mi = p_iptal_mi WHERE id = p_id;
END //

CREATE PROCEDURE sp_satislar_sil(IN p_id INT)
BEGIN
    UPDATE satislar SET iptal_mi = 1 WHERE id = p_id;
END //

CREATE PROCEDURE sp_satislar_listele(IN p_baslangic_tarihi DATETIME, IN p_bitis_tarihi DATETIME, IN p_musteri_id INT, IN p_odeme_yontemi VARCHAR(50), IN p_limit INT, IN p_offset INT)
BEGIN
    SELECT
        s.id, s.tarih, s.toplam_tutar, s.toplam_maliyet, s.indirim,
        s.odeme_yontemi, s.musteri_id, s.iptal_mi,
        m.ad_soyad AS musteri_adi, m.arac_plakasi,
        (s.toplam_tutar - s.indirim - s.toplam_maliyet) AS kar
    FROM satislar s
    JOIN musteriler m ON m.id = s.musteri_id
    WHERE
        s.iptal_mi = 0
        AND (p_baslangic_tarihi IS NULL OR s.tarih >= p_baslangic_tarihi)
        AND (p_bitis_tarihi IS NULL OR s.tarih <= p_bitis_tarihi)
        AND (p_musteri_id IS NULL OR s.musteri_id = p_musteri_id)
        AND (p_odeme_yontemi IS NULL OR s.odeme_yontemi = p_odeme_yontemi)
    ORDER BY s.tarih DESC
    LIMIT p_limit OFFSET p_offset;
END //

CREATE PROCEDURE sp_satislar_getir(IN p_id INT)
BEGIN
    SELECT
        s.id, s.tarih, s.toplam_tutar, s.toplam_maliyet, s.indirim,
        s.odeme_yontemi, s.musteri_id, s.iptal_mi,
        m.ad_soyad AS musteri_adi, m.arac_plakasi,
        (s.toplam_tutar - s.indirim - s.toplam_maliyet) AS kar
    FROM satislar s
    JOIN musteriler m ON m.id = s.musteri_id
    WHERE s.id = p_id;
END //

DELIMITER ;

-- ###############################################
-- satis_kalemleri
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_satis_kalemleri_ekle(IN p_satis_id INT, IN p_urun_id INT, IN p_urun_adi_anlik VARCHAR(100), IN p_miktar INT, IN p_birim_fiyat DECIMAL(18,2), IN p_birim_maliyet DECIMAL(18,2))
BEGIN
    INSERT INTO satis_kalemleri (satis_id, urun_id, urun_adi_anlik, miktar, birim_fiyat, birim_maliyet) VALUES (p_satis_id, p_urun_id, p_urun_adi_anlik, p_miktar, p_birim_fiyat, p_birim_maliyet);
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_satis_kalemleri_guncelle(IN p_id INT, IN p_satis_id INT, IN p_urun_id INT, IN p_urun_adi_anlik VARCHAR(100), IN p_miktar INT, IN p_birim_fiyat DECIMAL(18,2), IN p_birim_maliyet DECIMAL(18,2), IN p_iptal_mi BOOLEAN)
BEGIN
    UPDATE satis_kalemleri SET satis_id = p_satis_id, urun_id = p_urun_id, urun_adi_anlik = p_urun_adi_anlik, miktar = p_miktar, birim_fiyat = p_birim_fiyat, birim_maliyet = p_birim_maliyet, iptal_mi = p_iptal_mi WHERE id = p_id;
END //

CREATE PROCEDURE sp_satis_kalemleri_sil(IN p_id INT)
BEGIN
    UPDATE satis_kalemleri SET iptal_mi = 1 WHERE id = p_id;
END //

CREATE PROCEDURE sp_satis_kalemleri_satisa_gore_listele(IN p_satis_id INT)
BEGIN
    SELECT id, satis_id, urun_id, urun_adi_anlik, miktar, birim_fiyat, birim_maliyet, iptal_mi,
           (miktar * birim_fiyat) AS toplam_fiyat,
           (miktar * birim_maliyet) AS toplam_maliyet
    FROM satis_kalemleri
    WHERE satis_id = p_satis_id;
END //

DELIMITER ;

-- ###############################################
-- giderler
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_giderler_ekle(IN p_aciklama VARCHAR(255), IN p_tutar DECIMAL(18,2))
BEGIN
    INSERT INTO giderler (aciklama, tutar) VALUES (p_aciklama, p_tutar);
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_giderler_guncelle(IN p_id INT, IN p_aciklama VARCHAR(255), IN p_tutar DECIMAL(18,2), IN p_tarih DATETIME)
BEGIN
    UPDATE giderler SET aciklama = p_aciklama, tutar = p_tutar, tarih = p_tarih WHERE id = p_id;
END //

CREATE PROCEDURE sp_giderler_sil(IN p_id INT)
BEGIN
    DELETE FROM giderler WHERE id = p_id;
END //

CREATE PROCEDURE sp_giderler_listele(IN p_baslangic_tarihi DATETIME, IN p_bitis_tarihi DATETIME, IN p_limit INT, IN p_offset INT)
BEGIN
    SELECT id, aciklama, tutar, tarih
    FROM giderler
    WHERE
        (p_baslangic_tarihi IS NULL OR tarih >= p_baslangic_tarihi)
        AND (p_bitis_tarihi IS NULL OR tarih <= p_bitis_tarihi)
    ORDER BY tarih DESC
    LIMIT p_limit OFFSET p_offset;
END //

CREATE PROCEDURE sp_giderler_getir(IN p_id INT)
BEGIN
    SELECT id, aciklama, tutar, tarih FROM giderler WHERE id = p_id;
END //

DELIMITER ;

-- ###############################################
-- iptal_kayitlari
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_iptal_kayitlari_ekle(IN p_kayit_turu VARCHAR(20), IN p_kayit_id INT, IN p_aciklama TEXT, IN p_iptal_edilen_miktar INT, IN p_iade_tutari DECIMAL(18,2), IN p_maliyet_tutari DECIMAL(18,2), IN p_iptal_eden VARCHAR(50))
BEGIN
    INSERT INTO iptal_kayitlari (kayit_turu, kayit_id, aciklama, iptal_edilen_miktar, iade_tutari, maliyet_tutari, iptal_eden)
    VALUES (p_kayit_turu, p_kayit_id, p_aciklama, p_iptal_edilen_miktar, p_iade_tutari, p_maliyet_tutari, p_iptal_eden);
END //

CREATE PROCEDURE sp_iptal_kayitlari_listele(IN p_limit INT, IN p_offset INT)
BEGIN
    SELECT id, tarih, kayit_turu, kayit_id, aciklama, iptal_edilen_miktar, iade_tutari, maliyet_tutari, iptal_eden
    FROM iptal_kayitlari
    ORDER BY tarih DESC
    LIMIT p_limit OFFSET p_offset;
END //

DELIMITER ;

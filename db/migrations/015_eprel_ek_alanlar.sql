-- ─────────────────────────────────────────────────────────────────────────────
-- 015 — EPREL ek alanlar: yük indeksi, hız kodu, ekstra yük, üretim yılı
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE urunler
    ADD COLUMN yuk_indeksi VARCHAR(10) NULL AFTER ebat,
    ADD COLUMN hiz_kodu VARCHAR(5) NULL AFTER yuk_indeksi,
    ADD COLUMN ekstra_yuk TINYINT(1) NOT NULL DEFAULT 0 AFTER hiz_kodu,
    ADD COLUMN uretim_yili INT NULL AFTER ekstra_yuk;

-- ═══ SP'leri yeniden oluştur (yeni kolonlar dahil) ═══

-- sp_urunler_ekle
DROP PROCEDURE IF EXISTS sp_urunler_ekle;
DELIMITER //
CREATE PROCEDURE sp_urunler_ekle(
    IN p_barkod_qr VARCHAR(100),
    IN p_ad VARCHAR(100),
    IN p_ebat VARCHAR(50),
    IN p_yuk_indeksi VARCHAR(10),
    IN p_hiz_kodu VARCHAR(5),
    IN p_ekstra_yuk BOOLEAN,
    IN p_uretim_yili INT,
    IN p_aciklama TEXT,
    IN p_satis_fiyati DECIMAL(18,2),
    IN p_maliyet_fiyati DECIMAL(18,2),
    IN p_maliyet_bilinmiyor BOOLEAN,
    IN p_guncel_borctan BOOLEAN,
    IN p_stok INT,
    IN p_fiziksel_urun_mu BOOLEAN,
    IN p_resim_yolu VARCHAR(255),
    IN p_urun_tipi_id INT,
    IN p_marka_id INT,
    IN p_marka_modeli_id INT
)
BEGIN
    INSERT INTO urunler (
        barkod_qr, ad, ebat, yuk_indeksi, hiz_kodu, ekstra_yuk, uretim_yili,
        aciklama, satis_fiyati, maliyet_fiyati, maliyet_bilinmiyor, guncel_borctan,
        stok, fiziksel_urun_mu, resim_yolu,
        urun_tipi_id, marka_id, marka_modeli_id
    ) VALUES (
        p_barkod_qr, p_ad, p_ebat, p_yuk_indeksi, p_hiz_kodu, p_ekstra_yuk, p_uretim_yili,
        p_aciklama, p_satis_fiyati, p_maliyet_fiyati, p_maliyet_bilinmiyor, p_guncel_borctan,
        p_stok, p_fiziksel_urun_mu, p_resim_yolu,
        p_urun_tipi_id, p_marka_id, p_marka_modeli_id
    );
    SELECT LAST_INSERT_ID() AS id;
END //
DELIMITER ;

-- sp_urunler_guncelle
DROP PROCEDURE IF EXISTS sp_urunler_guncelle;
DELIMITER //
CREATE PROCEDURE sp_urunler_guncelle(
    IN p_id INT,
    IN p_barkod_qr VARCHAR(100),
    IN p_ad VARCHAR(100),
    IN p_ebat VARCHAR(50),
    IN p_yuk_indeksi VARCHAR(10),
    IN p_hiz_kodu VARCHAR(5),
    IN p_ekstra_yuk BOOLEAN,
    IN p_uretim_yili INT,
    IN p_aciklama TEXT,
    IN p_satis_fiyati DECIMAL(18,2),
    IN p_maliyet_fiyati DECIMAL(18,2),
    IN p_maliyet_bilinmiyor BOOLEAN,
    IN p_guncel_borctan BOOLEAN,
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
        yuk_indeksi = p_yuk_indeksi,
        hiz_kodu = p_hiz_kodu,
        ekstra_yuk = p_ekstra_yuk,
        uretim_yili = p_uretim_yili,
        aciklama = p_aciklama,
        satis_fiyati = p_satis_fiyati,
        maliyet_fiyati = p_maliyet_fiyati,
        maliyet_bilinmiyor = p_maliyet_bilinmiyor,
        guncel_borctan = p_guncel_borctan,
        stok = p_stok,
        fiziksel_urun_mu = p_fiziksel_urun_mu,
        resim_yolu = p_resim_yolu,
        silindi_mi = p_silindi_mi,
        urun_tipi_id = p_urun_tipi_id,
        marka_id = p_marka_id,
        marka_modeli_id = p_marka_modeli_id
    WHERE id = p_id;
END //
DELIMITER ;

-- sp_urunler_getir
DROP PROCEDURE IF EXISTS sp_urunler_getir;
DELIMITER //
CREATE PROCEDURE sp_urunler_getir(IN p_id INT)
BEGIN
    SELECT
        u.id, u.barkod_qr, u.ad, u.ebat,
        u.yuk_indeksi, u.hiz_kodu, u.ekstra_yuk, u.uretim_yili,
        u.aciklama, u.satis_fiyati, u.maliyet_fiyati,
        u.maliyet_bilinmiyor, u.guncel_borctan,
        u.stok, u.fiziksel_urun_mu,
        u.resim_yolu, u.silindi_mi,
        u.urun_tipi_id, u.marka_id, u.marka_modeli_id,
        t.ad AS tip_adi, m.ad AS marka_adi, mm.ad AS model_adi, mm.mevsim
    FROM urunler u
    JOIN urun_tipleri t ON t.id = u.urun_tipi_id
    JOIN urun_markalari m ON m.id = u.marka_id
    JOIN urun_marka_modelleri mm ON mm.id = u.marka_modeli_id
    WHERE u.id = p_id;
END //
DELIMITER ;

-- sp_urunler_listele
DROP PROCEDURE IF EXISTS sp_urunler_listele;
DELIMITER //
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
        u.id, u.barkod_qr, u.ad, u.ebat,
        u.yuk_indeksi, u.hiz_kodu, u.ekstra_yuk, u.uretim_yili,
        u.satis_fiyati, u.maliyet_fiyati,
        u.maliyet_bilinmiyor, u.guncel_borctan,
        u.stok, u.fiziksel_urun_mu,
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
DELIMITER ;

-- sp_urunler_barkod_ara
DROP PROCEDURE IF EXISTS sp_urunler_barkod_ara;
DELIMITER //
CREATE PROCEDURE sp_urunler_barkod_ara(IN p_barkod VARCHAR(100))
BEGIN
    SELECT
        u.id, u.barkod_qr, u.ad, u.ebat,
        u.yuk_indeksi, u.hiz_kodu, u.ekstra_yuk, u.uretim_yili,
        u.satis_fiyati, u.maliyet_fiyati,
        u.maliyet_bilinmiyor, u.guncel_borctan,
        u.stok, u.fiziksel_urun_mu,
        u.urun_tipi_id, u.marka_id, u.marka_modeli_id,
        t.ad AS tip_adi, m.ad AS marka_adi, mm.ad AS model_adi, mm.mevsim
    FROM urunler u
    JOIN urun_tipleri t ON t.id = u.urun_tipi_id
    JOIN urun_markalari m ON m.id = u.marka_id
    JOIN urun_marka_modelleri mm ON mm.id = u.marka_modeli_id
    WHERE u.barkod_qr = p_barkod AND u.silindi_mi = 0;
END //
DELIMITER ;

-- sp_urun_eprel_bul (yeni alanlar dahil)
DROP PROCEDURE IF EXISTS sp_urun_eprel_bul;
DELIMITER //
CREATE PROCEDURE sp_urun_eprel_bul(IN p_eprel_no VARCHAR(50))
BEGIN
    SELECT u.id, u.ad, u.ebat, u.yuk_indeksi, u.hiz_kodu, u.ekstra_yuk, u.uretim_yili,
           u.stok, u.satis_fiyati, u.maliyet_fiyati, u.barkod_qr
    FROM urunler u
    WHERE u.barkod_qr = p_eprel_no AND u.silindi_mi = 0
    LIMIT 1;
END //
DELIMITER ;

-- ═══ Özellik 2: Akıllı stok eşleştirme SP'si ═══

DROP PROCEDURE IF EXISTS sp_urun_tam_eslesme_bul;
DELIMITER //
CREATE PROCEDURE sp_urun_tam_eslesme_bul(
    IN p_marka_ad VARCHAR(100),
    IN p_model_ad VARCHAR(200),
    IN p_ebat VARCHAR(50),
    IN p_yuk_indeksi VARCHAR(10),
    IN p_hiz_kodu VARCHAR(5),
    IN p_ekstra_yuk BOOLEAN,
    IN p_uretim_yili INT
)
BEGIN
    SELECT u.id, u.ad, u.satis_fiyati, u.maliyet_fiyati, u.barkod_qr, u.silindi_mi
    FROM urunler u
    JOIN urun_markalari m ON m.id = u.marka_id
    JOIN urun_marka_modelleri mm ON mm.id = u.marka_modeli_id
    WHERE m.ad = p_marka_ad
      AND mm.ad = p_model_ad
      AND u.ebat = p_ebat
      AND (u.yuk_indeksi = p_yuk_indeksi OR (u.yuk_indeksi IS NULL AND p_yuk_indeksi IS NULL))
      AND (u.hiz_kodu = p_hiz_kodu OR (u.hiz_kodu IS NULL AND p_hiz_kodu IS NULL))
      AND u.ekstra_yuk = IFNULL(p_ekstra_yuk, 0)
      AND (u.uretim_yili = p_uretim_yili OR (u.uretim_yili IS NULL AND p_uretim_yili IS NULL))
    LIMIT 1;
END //
DELIMITER ;

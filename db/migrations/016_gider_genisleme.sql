-- =============================================
-- 016 — GİDER GENİŞLEME (Lastik dışı ürün alımları)
-- =============================================

USE DijitalLastikServisiDB;

ALTER TABLE giderler
    ADD COLUMN kategori VARCHAR(50) NULL AFTER tarih,
    ADD COLUMN urun_adi VARCHAR(100) NULL AFTER kategori,
    ADD COLUMN marka VARCHAR(100) NULL AFTER urun_adi,
    ADD COLUMN alis_fiyati DECIMAL(18,2) NULL AFTER marka,
    ADD COLUMN satis_fiyati DECIMAL(18,2) NULL AFTER alis_fiyati,
    ADD COLUMN yil INT NULL AFTER satis_fiyati,
    ADD COLUMN maliyet_bilinmiyor TINYINT(1) DEFAULT 0 AFTER yil;

-- SP'leri yeniden oluştur

DELIMITER //

DROP PROCEDURE IF EXISTS sp_giderler_ekle //
CREATE PROCEDURE sp_giderler_ekle(
    IN p_aciklama VARCHAR(255),
    IN p_tutar DECIMAL(18,2),
    IN p_kategori VARCHAR(50),
    IN p_urun_adi VARCHAR(100),
    IN p_marka VARCHAR(100),
    IN p_alis_fiyati DECIMAL(18,2),
    IN p_satis_fiyati DECIMAL(18,2),
    IN p_yil INT,
    IN p_maliyet_bilinmiyor TINYINT(1)
)
BEGIN
    INSERT INTO giderler (aciklama, tutar, kategori, urun_adi, marka, alis_fiyati, satis_fiyati, yil, maliyet_bilinmiyor)
    VALUES (p_aciklama, p_tutar, p_kategori, p_urun_adi, p_marka, p_alis_fiyati, p_satis_fiyati, p_yil, p_maliyet_bilinmiyor);
    SELECT LAST_INSERT_ID() AS id;
END //

DROP PROCEDURE IF EXISTS sp_giderler_guncelle //
CREATE PROCEDURE sp_giderler_guncelle(
    IN p_id INT,
    IN p_aciklama VARCHAR(255),
    IN p_tutar DECIMAL(18,2),
    IN p_tarih DATETIME,
    IN p_kategori VARCHAR(50),
    IN p_urun_adi VARCHAR(100),
    IN p_marka VARCHAR(100),
    IN p_alis_fiyati DECIMAL(18,2),
    IN p_satis_fiyati DECIMAL(18,2),
    IN p_yil INT,
    IN p_maliyet_bilinmiyor TINYINT(1)
)
BEGIN
    UPDATE giderler SET
        aciklama = p_aciklama,
        tutar = p_tutar,
        tarih = p_tarih,
        kategori = p_kategori,
        urun_adi = p_urun_adi,
        marka = p_marka,
        alis_fiyati = p_alis_fiyati,
        satis_fiyati = p_satis_fiyati,
        yil = p_yil,
        maliyet_bilinmiyor = p_maliyet_bilinmiyor
    WHERE id = p_id;
END //

DROP PROCEDURE IF EXISTS sp_giderler_listele //
CREATE PROCEDURE sp_giderler_listele(
    IN p_baslangic_tarihi DATETIME,
    IN p_bitis_tarihi DATETIME,
    IN p_limit INT,
    IN p_offset INT,
    IN p_kategori VARCHAR(50)
)
BEGIN
    SELECT id, aciklama, tutar, tarih, kategori, urun_adi, marka, alis_fiyati, satis_fiyati, yil, maliyet_bilinmiyor
    FROM giderler
    WHERE
        (p_baslangic_tarihi IS NULL OR tarih >= p_baslangic_tarihi)
        AND (p_bitis_tarihi IS NULL OR tarih <= p_bitis_tarihi)
        AND (p_kategori IS NULL OR p_kategori = '' OR kategori = p_kategori)
    ORDER BY tarih DESC
    LIMIT p_limit OFFSET p_offset;
END //

DROP PROCEDURE IF EXISTS sp_giderler_getir //
CREATE PROCEDURE sp_giderler_getir(IN p_id INT)
BEGIN
    SELECT id, aciklama, tutar, tarih, kategori, urun_adi, marka, alis_fiyati, satis_fiyati, yil, maliyet_bilinmiyor
    FROM giderler WHERE id = p_id;
END //

DELIMITER ;

-- ─────────────────────────────────────────────────────────────────────────────
-- 008_eprel.sql  —  EPREL QR entegrasyonu: find-or-create hiyerarşi SP'leri
-- ─────────────────────────────────────────────────────────────────────────────

DELIMITER //

-- Ürün tipini ada göre bul, yoksa oluştur → id döner
DROP PROCEDURE IF EXISTS sp_urun_tipi_bul_veya_olustur //
CREATE PROCEDURE sp_urun_tipi_bul_veya_olustur(IN p_ad VARCHAR(100))
BEGIN
    DECLARE v_id INT DEFAULT NULL;
    SELECT id INTO v_id FROM urun_tipleri WHERE ad = p_ad LIMIT 1;
    IF v_id IS NULL THEN
        INSERT INTO urun_tipleri(ad) VALUES(p_ad);
        SET v_id = LAST_INSERT_ID();
    END IF;
    SELECT v_id AS id;
END //

-- Markayı tip+ada göre bul, yoksa oluştur → id döner
DROP PROCEDURE IF EXISTS sp_urun_markasi_bul_veya_olustur //
CREATE PROCEDURE sp_urun_markasi_bul_veya_olustur(IN p_tipi_id INT, IN p_ad VARCHAR(100))
BEGIN
    DECLARE v_id INT DEFAULT NULL;
    SELECT id INTO v_id FROM urun_markalari
    WHERE urun_tipi_id = p_tipi_id AND ad = p_ad LIMIT 1;
    IF v_id IS NULL THEN
        INSERT INTO urun_markalari(urun_tipi_id, ad) VALUES(p_tipi_id, p_ad);
        SET v_id = LAST_INSERT_ID();
    END IF;
    SELECT v_id AS id;
END //

-- Modeli marka+ada göre bul, yoksa oluştur → id döner
DROP PROCEDURE IF EXISTS sp_urun_modeli_bul_veya_olustur //
CREATE PROCEDURE sp_urun_modeli_bul_veya_olustur(
    IN p_marka_id INT,
    IN p_ad       VARCHAR(200),
    IN p_mevsim   VARCHAR(50)
)
BEGIN
    DECLARE v_id INT DEFAULT NULL;
    SELECT id INTO v_id FROM urun_marka_modelleri
    WHERE marka_id = p_marka_id AND ad = p_ad LIMIT 1;
    IF v_id IS NULL THEN
        INSERT INTO urun_marka_modelleri(marka_id, ad, mevsim)
        VALUES(p_marka_id, p_ad, p_mevsim);
        SET v_id = LAST_INSERT_ID();
    END IF;
    SELECT v_id AS id;
END //

-- EPREL kayıt numarasına göre ürün bul (barkod_qr'da saklanır)
DROP PROCEDURE IF EXISTS sp_urun_eprel_bul //
CREATE PROCEDURE sp_urun_eprel_bul(IN p_eprel_no VARCHAR(50))
BEGIN
    SELECT u.id, u.ad, u.ebat, u.stok, u.satis_fiyati, u.maliyet_fiyati, u.barkod_qr
    FROM urunler u
    WHERE u.barkod_qr = p_eprel_no AND u.silindi_mi = 0
    LIMIT 1;
END //

DELIMITER ;

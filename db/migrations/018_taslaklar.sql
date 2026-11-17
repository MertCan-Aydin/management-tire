-- =============================================
-- 018 — TASLAKLAR (Yarım kalan form verileri)
-- =============================================

USE DijitalLastikServisiDB;

CREATE TABLE IF NOT EXISTS taslaklar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kullanici_id INT NOT NULL,
    form_tipi VARCHAR(50) NOT NULL,
    baslik VARCHAR(200) NULL,
    veri JSON NOT NULL,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    guncelleme DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_kullanici (kullanici_id),
    INDEX idx_form_tipi (form_tipi)
);

DELIMITER //

DROP PROCEDURE IF EXISTS sp_taslak_ekle //
CREATE PROCEDURE sp_taslak_ekle(
    IN p_kullanici_id INT,
    IN p_form_tipi VARCHAR(50),
    IN p_baslik VARCHAR(200),
    IN p_veri JSON
)
BEGIN
    INSERT INTO taslaklar (kullanici_id, form_tipi, baslik, veri)
    VALUES (p_kullanici_id, p_form_tipi, p_baslik, p_veri);
    SELECT LAST_INSERT_ID() AS id;
END //

DROP PROCEDURE IF EXISTS sp_taslak_guncelle //
CREATE PROCEDURE sp_taslak_guncelle(
    IN p_id INT,
    IN p_baslik VARCHAR(200),
    IN p_veri JSON
)
BEGIN
    UPDATE taslaklar SET baslik = p_baslik, veri = p_veri WHERE id = p_id;
END //

DROP PROCEDURE IF EXISTS sp_taslak_listele //
CREATE PROCEDURE sp_taslak_listele(
    IN p_kullanici_id INT,
    IN p_form_tipi VARCHAR(50)
)
BEGIN
    SELECT id, kullanici_id, form_tipi, baslik, veri, tarih, guncelleme
    FROM taslaklar
    WHERE kullanici_id = p_kullanici_id
      AND (p_form_tipi IS NULL OR p_form_tipi = '' OR form_tipi = p_form_tipi)
    ORDER BY guncelleme DESC;
END //

DROP PROCEDURE IF EXISTS sp_taslak_getir //
CREATE PROCEDURE sp_taslak_getir(IN p_id INT)
BEGIN
    SELECT id, kullanici_id, form_tipi, baslik, veri, tarih, guncelleme
    FROM taslaklar WHERE id = p_id;
END //

DROP PROCEDURE IF EXISTS sp_taslak_sil //
CREATE PROCEDURE sp_taslak_sil(IN p_id INT)
BEGIN
    DELETE FROM taslaklar WHERE id = p_id;
END //

DELIMITER ;

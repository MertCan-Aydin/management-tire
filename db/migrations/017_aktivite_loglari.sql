-- =============================================
-- 017 — AKTİVİTE LOGLARI
-- =============================================

USE DijitalLastikServisiDB;

CREATE TABLE IF NOT EXISTS aktivite_loglari (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kullanici_id INT NULL,
    islem_tipi VARCHAR(50) NOT NULL,
    sayfa VARCHAR(100) NULL,
    detay TEXT NULL,
    ip_adresi VARCHAR(45) NULL,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tarih (tarih),
    INDEX idx_kullanici (kullanici_id)
);

DELIMITER //

DROP PROCEDURE IF EXISTS sp_aktivite_log_ekle //
CREATE PROCEDURE sp_aktivite_log_ekle(
    IN p_kullanici_id INT,
    IN p_islem_tipi VARCHAR(50),
    IN p_sayfa VARCHAR(100),
    IN p_detay TEXT,
    IN p_ip_adresi VARCHAR(45)
)
BEGIN
    INSERT INTO aktivite_loglari (kullanici_id, islem_tipi, sayfa, detay, ip_adresi)
    VALUES (p_kullanici_id, p_islem_tipi, p_sayfa, p_detay, p_ip_adresi);
    SELECT LAST_INSERT_ID() AS id;
END //

DROP PROCEDURE IF EXISTS sp_aktivite_log_listele //
CREATE PROCEDURE sp_aktivite_log_listele(
    IN p_kullanici_id INT,
    IN p_islem_tipi VARCHAR(50),
    IN p_baslangic DATETIME,
    IN p_bitis DATETIME,
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    SELECT id, kullanici_id, islem_tipi, sayfa, detay, ip_adresi, tarih
    FROM aktivite_loglari
    WHERE
        (p_kullanici_id IS NULL OR kullanici_id = p_kullanici_id)
        AND (p_islem_tipi IS NULL OR p_islem_tipi = '' OR islem_tipi = p_islem_tipi)
        AND (p_baslangic IS NULL OR tarih >= p_baslangic)
        AND (p_bitis IS NULL OR tarih <= p_bitis)
    ORDER BY tarih DESC
    LIMIT p_limit OFFSET p_offset;
END //

DELIMITER ;

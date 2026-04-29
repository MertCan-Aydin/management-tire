-- =============================================
-- 007 — PIN LOGIN SP
-- Tek kullanıcılı sistemde kullanıcı adı
-- sorulmaksızın sadece PIN ile giriş için.
-- =============================================

USE DijitalLastikServisiDB;

DROP PROCEDURE IF EXISTS sp_admin_kullanici_getir;

DELIMITER //

CREATE PROCEDURE sp_admin_kullanici_getir()
BEGIN
    -- Sistemdeki tek aktif admin kullanıcıyı döner.
    -- PIN doğrulaması için kullanılır; kullanıcı adı sorulmaz.
    SELECT id, kullanici_adi, parola_hash, rol, aktif_mi
    FROM kullanicilar
    WHERE rol = 'admin' AND aktif_mi = 1
    ORDER BY id ASC
    LIMIT 1;
END //

DELIMITER ;

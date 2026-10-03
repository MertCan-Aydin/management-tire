-- =============================================
-- 005 — KİMLİK DOĞRULAMA TABLOLARI VE SP'LERİ
-- =============================================

USE DijitalLastikServisiDB;

CREATE TABLE IF NOT EXISTS kullanicilar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kullanici_adi VARCHAR(50) NOT NULL UNIQUE,
    parola_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'admin' CHECK (rol IN ('admin', 'kullanici')),
    aktif_mi BOOLEAN DEFAULT 1,
    olusturulma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    son_giris_tarihi DATETIME NULL
);

CREATE TABLE IF NOT EXISTS refresh_tokenlar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kullanici_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    olusturulma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    son_kullanma_tarihi DATETIME NOT NULL,
    iptal_mi BOOLEAN DEFAULT 0,
    FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id)
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokenlar_kullanici ON refresh_tokenlar(kullanici_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokenlar_son_kullanma ON refresh_tokenlar(son_kullanma_tarihi);

-- ###############################################
-- AUTH STORED PROCEDURE'LERİ
-- ###############################################

DELIMITER //

CREATE PROCEDURE sp_kullanici_olustur(
    IN p_kullanici_adi VARCHAR(50),
    IN p_parola_hash VARCHAR(255),
    IN p_rol VARCHAR(20)
)
BEGIN
    INSERT INTO kullanicilar (kullanici_adi, parola_hash, rol)
    VALUES (p_kullanici_adi, p_parola_hash, p_rol);
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_kullanici_adi_ile_getir(IN p_kullanici_adi VARCHAR(50))
BEGIN
    SELECT id, kullanici_adi, parola_hash, rol, aktif_mi, son_giris_tarihi
    FROM kullanicilar
    WHERE kullanici_adi = p_kullanici_adi AND aktif_mi = 1;
END //

CREATE PROCEDURE sp_kullanici_getir(IN p_id INT)
BEGIN
    SELECT id, kullanici_adi, rol, aktif_mi, olusturulma_tarihi, son_giris_tarihi
    FROM kullanicilar
    WHERE id = p_id;
END //

CREATE PROCEDURE sp_kullanici_giris_tarihi_guncelle(IN p_id INT)
BEGIN
    UPDATE kullanicilar SET son_giris_tarihi = CURRENT_TIMESTAMP WHERE id = p_id;
END //

CREATE PROCEDURE sp_kullanici_parola_guncelle(IN p_id INT, IN p_yeni_parola_hash VARCHAR(255))
BEGIN
    UPDATE kullanicilar SET parola_hash = p_yeni_parola_hash WHERE id = p_id;
END //

-- Refresh token işlemleri
CREATE PROCEDURE sp_refresh_token_ekle(
    IN p_kullanici_id INT,
    IN p_token_hash VARCHAR(255),
    IN p_son_kullanma_tarihi DATETIME
)
BEGIN
    INSERT INTO refresh_tokenlar (kullanici_id, token_hash, son_kullanma_tarihi)
    VALUES (p_kullanici_id, p_token_hash, p_son_kullanma_tarihi);
END //

CREATE PROCEDURE sp_refresh_token_getir(IN p_token_hash VARCHAR(255))
BEGIN
    SELECT id, kullanici_id, token_hash, olusturulma_tarihi, son_kullanma_tarihi, iptal_mi
    FROM refresh_tokenlar
    WHERE token_hash = p_token_hash
      AND iptal_mi = 0
      AND son_kullanma_tarihi > CURRENT_TIMESTAMP;
END //

CREATE PROCEDURE sp_refresh_token_iptal(IN p_token_hash VARCHAR(255))
BEGIN
    UPDATE refresh_tokenlar SET iptal_mi = 1 WHERE token_hash = p_token_hash;
END //

CREATE PROCEDURE sp_refresh_tokenlari_kullaniciya_gore_iptal(IN p_kullanici_id INT)
BEGIN
    -- Kullanıcı çıkış yaptığında tüm aktif token'larını iptal et
    UPDATE refresh_tokenlar SET iptal_mi = 1 WHERE kullanici_id = p_kullanici_id AND iptal_mi = 0;
END //

CREATE PROCEDURE sp_suresi_gecmis_tokenlari_temizle()
BEGIN
    DELETE FROM refresh_tokenlar WHERE son_kullanma_tarihi < CURRENT_TIMESTAMP;
END //

DELIMITER ;

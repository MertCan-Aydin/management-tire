-- ─────────────────────────────────────────────────────────────────────────────
-- 009_lastik_oteli.sql  —  Lastik Oteli modülü
-- ─────────────────────────────────────────────────────────────────────────────

-- Tablo
CREATE TABLE IF NOT EXISTS lastik_oteli (
    id                  INT          AUTO_INCREMENT PRIMARY KEY,
    musteri_id          INT          NULL,
    musteri_adi_anlik   VARCHAR(100) NOT NULL,
    arac_plakasi        VARCHAR(20)  NULL,
    raf_kodu            VARCHAR(10)  NOT NULL,
    lastik_bilgisi      VARCHAR(200) NULL,
    lastik_adedi        INT          NOT NULL DEFAULT 4,
    sezon               ENUM('Yaz','Kış') NOT NULL,
    giris_tarihi        DATE         NOT NULL,
    cikis_tarihi        DATE         NULL,
    notlar              TEXT         NULL,
    aktif_mi            TINYINT(1)   NOT NULL DEFAULT 1,
    olusturulma_tarihi  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_oteli_musteri
        FOREIGN KEY (musteri_id) REFERENCES musteriler(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX IF NOT EXISTS idx_oteli_raf   ON lastik_oteli(raf_kodu);
CREATE INDEX IF NOT EXISTS idx_oteli_aktif ON lastik_oteli(aktif_mi);

DELIMITER //

-- ── Ekle ─────────────────────────────────────────────────────────────────────
DROP PROCEDURE IF EXISTS sp_lastik_oteli_ekle //
CREATE PROCEDURE sp_lastik_oteli_ekle(
    IN p_musteri_id         INT,
    IN p_musteri_adi_anlik  VARCHAR(100),
    IN p_arac_plakasi       VARCHAR(20),
    IN p_raf_kodu           VARCHAR(10),
    IN p_lastik_bilgisi     VARCHAR(200),
    IN p_lastik_adedi       INT,
    IN p_sezon              VARCHAR(10),
    IN p_giris_tarihi       DATE,
    IN p_notlar             TEXT
)
BEGIN
    DECLARE v_dolu INT DEFAULT 0;
    SELECT COUNT(*) INTO v_dolu
    FROM lastik_oteli
    WHERE raf_kodu = p_raf_kodu AND aktif_mi = 1;

    IF v_dolu > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Bu raf kodu zaten dolu (aktif kayıt var)';
    END IF;

    INSERT INTO lastik_oteli (
        musteri_id, musteri_adi_anlik, arac_plakasi, raf_kodu,
        lastik_bilgisi, lastik_adedi, sezon, giris_tarihi, notlar
    ) VALUES (
        p_musteri_id, p_musteri_adi_anlik, p_arac_plakasi, p_raf_kodu,
        p_lastik_bilgisi, p_lastik_adedi, p_sezon, p_giris_tarihi, p_notlar
    );
    SELECT LAST_INSERT_ID() AS id;
END //

-- ── Listele ──────────────────────────────────────────────────────────────────
DROP PROCEDURE IF EXISTS sp_lastik_oteli_listele //
CREATE PROCEDURE sp_lastik_oteli_listele(
    IN p_sadece_aktif TINYINT,
    IN p_arama        VARCHAR(100),
    IN p_limit        INT,
    IN p_offset       INT
)
BEGIN
    SELECT
        lo.id,
        lo.raf_kodu,
        lo.musteri_id,
        COALESCE(m.ad_soyad, lo.musteri_adi_anlik) AS musteri_adi,
        COALESCE(m.arac_plakasi, lo.arac_plakasi)  AS arac_plakasi,
        lo.lastik_bilgisi,
        lo.lastik_adedi,
        lo.sezon,
        lo.giris_tarihi,
        lo.cikis_tarihi,
        lo.notlar,
        lo.aktif_mi
    FROM lastik_oteli lo
    LEFT JOIN musteriler m ON lo.musteri_id = m.id
    WHERE
        (p_sadece_aktif = 0 OR lo.aktif_mi = 1)
        AND (
            p_arama IS NULL OR p_arama = '' OR
            lo.raf_kodu LIKE CONCAT('%', p_arama, '%') OR
            COALESCE(m.ad_soyad, lo.musteri_adi_anlik) LIKE CONCAT('%', p_arama, '%') OR
            COALESCE(m.arac_plakasi, lo.arac_plakasi)  LIKE CONCAT('%', p_arama, '%')
        )
    ORDER BY lo.aktif_mi DESC, lo.raf_kodu ASC
    LIMIT p_limit OFFSET p_offset;
END //

-- ── Getir ────────────────────────────────────────────────────────────────────
DROP PROCEDURE IF EXISTS sp_lastik_oteli_getir //
CREATE PROCEDURE sp_lastik_oteli_getir(IN p_id INT)
BEGIN
    SELECT
        lo.id, lo.raf_kodu, lo.musteri_id,
        COALESCE(m.ad_soyad, lo.musteri_adi_anlik) AS musteri_adi,
        COALESCE(m.arac_plakasi, lo.arac_plakasi)  AS arac_plakasi,
        lo.lastik_bilgisi, lo.lastik_adedi, lo.sezon,
        lo.giris_tarihi, lo.cikis_tarihi, lo.notlar, lo.aktif_mi
    FROM lastik_oteli lo
    LEFT JOIN musteriler m ON lo.musteri_id = m.id
    WHERE lo.id = p_id;
END //

-- ── Teslim Et ────────────────────────────────────────────────────────────────
DROP PROCEDURE IF EXISTS sp_lastik_oteli_teslim_et //
CREATE PROCEDURE sp_lastik_oteli_teslim_et(
    IN p_id           INT,
    IN p_cikis_tarihi DATE
)
BEGIN
    UPDATE lastik_oteli
    SET aktif_mi = 0, cikis_tarihi = p_cikis_tarihi
    WHERE id = p_id;
END //

-- ── Sil ──────────────────────────────────────────────────────────────────────
DROP PROCEDURE IF EXISTS sp_lastik_oteli_sil //
CREATE PROCEDURE sp_lastik_oteli_sil(IN p_id INT)
BEGIN
    DELETE FROM lastik_oteli WHERE id = p_id;
END //

-- ── Raf kontrol ──────────────────────────────────────────────────────────────
DROP PROCEDURE IF EXISTS sp_lastik_oteli_raf_kontrol //
CREATE PROCEDURE sp_lastik_oteli_raf_kontrol(IN p_raf_kodu VARCHAR(10))
BEGIN
    SELECT lo.id, lo.raf_kodu,
           COALESCE(m.ad_soyad, lo.musteri_adi_anlik) AS musteri_adi,
           lo.lastik_bilgisi, lo.sezon, lo.aktif_mi
    FROM lastik_oteli lo
    LEFT JOIN musteriler m ON lo.musteri_id = m.id
    WHERE lo.raf_kodu = p_raf_kodu AND lo.aktif_mi = 1
    LIMIT 1;
END //

DELIMITER ;

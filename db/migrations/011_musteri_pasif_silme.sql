-- ─────────────────────────────────────────────────────────────────────────────
-- 011_musteri_pasif_silme.sql  —  Müşteriler için pasif silme (soft delete)
-- ─────────────────────────────────────────────────────────────────────────────
-- Satışı olan müşteri satislar.musteri_id yabancı anahtarı yüzünden
-- silinemiyordu. Artık silme kaydı kaldırmaz, silindi_mi = 1 yapar; satış
-- geçmişi ve raporlar müşteri adıyla birlikte korunur.
--
-- telefon ve arac_plakasi UNIQUE olduğu için:
--   * Silinmiş bir müşterinin telefonuyla yeni müşteri eklenirse eski kayıt
--     yeni bilgilerle yeniden aktif edilir (satış geçmişi geri gelir).
--   * Silinmiş bir müşterinin plakası başka bir müşteriye verilirse plaka
--     silinmiş kayıttan boşaltılır.
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE musteriler ADD COLUMN IF NOT EXISTS silindi_mi BOOLEAN NOT NULL DEFAULT 0;

DELIMITER //

DROP PROCEDURE IF EXISTS sp_musteriler_sil //
CREATE PROCEDURE sp_musteriler_sil(IN p_id INT)
BEGIN
    UPDATE musteriler SET silindi_mi = 1 WHERE id = p_id;
END //

DROP PROCEDURE IF EXISTS sp_musteriler_ekle //
CREATE PROCEDURE sp_musteriler_ekle(IN p_ad_soyad VARCHAR(100), IN p_telefon VARCHAR(20), IN p_arac_markasi VARCHAR(50), IN p_arac_plakasi VARCHAR(20), IN p_notlar TEXT)
BEGIN
    DECLARE v_id INT;

    UPDATE musteriler SET arac_plakasi = NULL
    WHERE silindi_mi = 1 AND arac_plakasi = p_arac_plakasi AND telefon <> p_telefon;

    SET v_id = (SELECT id FROM musteriler WHERE telefon = p_telefon AND silindi_mi = 1);

    IF v_id IS NOT NULL THEN
        UPDATE musteriler
        SET ad_soyad = p_ad_soyad, arac_markasi = p_arac_markasi, arac_plakasi = p_arac_plakasi, notlar = p_notlar, silindi_mi = 0
        WHERE id = v_id;
        SELECT v_id AS id;
    ELSE
        INSERT INTO musteriler (ad_soyad, telefon, arac_markasi, arac_plakasi, notlar) VALUES (p_ad_soyad, p_telefon, p_arac_markasi, p_arac_plakasi, p_notlar);
        SELECT LAST_INSERT_ID() AS id;
    END IF;
END //

DROP PROCEDURE IF EXISTS sp_musteriler_guncelle //
CREATE PROCEDURE sp_musteriler_guncelle(IN p_id INT, IN p_ad_soyad VARCHAR(100), IN p_telefon VARCHAR(20), IN p_arac_markasi VARCHAR(50), IN p_arac_plakasi VARCHAR(20), IN p_notlar TEXT)
BEGIN
    UPDATE musteriler SET arac_plakasi = NULL
    WHERE silindi_mi = 1 AND arac_plakasi = p_arac_plakasi AND id <> p_id;

    UPDATE musteriler SET ad_soyad = p_ad_soyad, telefon = p_telefon, arac_markasi = p_arac_markasi, arac_plakasi = p_arac_plakasi, notlar = p_notlar WHERE id = p_id;
END //

DROP PROCEDURE IF EXISTS sp_musteriler_listele //
CREATE PROCEDURE sp_musteriler_listele(IN p_arama VARCHAR(100), IN p_limit INT, IN p_offset INT)
BEGIN
    SELECT id, ad_soyad, telefon, arac_markasi, arac_plakasi, notlar
    FROM musteriler
    WHERE silindi_mi = 0
        AND (p_arama IS NULL OR ad_soyad LIKE CONCAT('%', p_arama, '%') OR telefon LIKE CONCAT('%', p_arama, '%') OR arac_plakasi LIKE CONCAT('%', p_arama, '%'))
    ORDER BY ad_soyad
    LIMIT p_limit OFFSET p_offset;
END //

DROP PROCEDURE IF EXISTS sp_musteriler_getir //
CREATE PROCEDURE sp_musteriler_getir(IN p_id INT)
BEGIN
    SELECT id, ad_soyad, telefon, arac_markasi, arac_plakasi, notlar FROM musteriler WHERE id = p_id AND silindi_mi = 0;
END //

DROP PROCEDURE IF EXISTS sp_musteriler_plaka_ara //
CREATE PROCEDURE sp_musteriler_plaka_ara(IN p_plaka VARCHAR(20))
BEGIN
    SELECT id, ad_soyad, telefon, arac_markasi, arac_plakasi, notlar FROM musteriler WHERE arac_plakasi = p_plaka AND silindi_mi = 0;
END //

DROP PROCEDURE IF EXISTS sp_musteriler_telefon_ara //
CREATE PROCEDURE sp_musteriler_telefon_ara(IN p_telefon VARCHAR(20))
BEGIN
    SELECT id, ad_soyad, telefon, arac_markasi, arac_plakasi, notlar FROM musteriler WHERE telefon = p_telefon AND silindi_mi = 0;
END //

-- Dashboard özeti: toplam müşteri yalnızca aktif müşterileri sayar
DROP PROCEDURE IF EXISTS sp_dashboard_ozet //
CREATE PROCEDURE sp_dashboard_ozet()
BEGIN
    SELECT
        -- Bugün
        (SELECT COALESCE(SUM(toplam_tutar - indirim), 0) FROM satislar WHERE DATE(tarih) = CURDATE() AND iptal_mi = 0) AS bugun_ciro,
        (SELECT COALESCE(SUM(toplam_tutar - indirim - toplam_maliyet), 0) FROM satislar WHERE DATE(tarih) = CURDATE() AND iptal_mi = 0) AS bugun_kar,
        (SELECT COUNT(*) FROM satislar WHERE DATE(tarih) = CURDATE() AND iptal_mi = 0) AS bugun_satis_adedi,
        -- Bu ay
        (SELECT COALESCE(SUM(toplam_tutar - indirim), 0) FROM satislar WHERE YEAR(tarih) = YEAR(CURDATE()) AND MONTH(tarih) = MONTH(CURDATE()) AND iptal_mi = 0) AS bu_ay_ciro,
        (SELECT COALESCE(SUM(toplam_tutar - indirim - toplam_maliyet), 0) FROM satislar WHERE YEAR(tarih) = YEAR(CURDATE()) AND MONTH(tarih) = MONTH(CURDATE()) AND iptal_mi = 0) AS bu_ay_kar,
        -- Tedarikçi toplam borç
        (SELECT COALESCE(SUM(guncel_borc), 0) FROM tedarikciler WHERE silindi_mi = 0) AS toplam_tedarikci_borcu,
        -- Stok değeri
        (SELECT COALESCE(SUM(stok * maliyet_fiyati), 0) FROM urunler WHERE silindi_mi = 0 AND fiziksel_urun_mu = 1) AS toplam_stok_degeri,
        -- Toplam müşteri
        (SELECT COUNT(*) FROM musteriler WHERE silindi_mi = 0) AS toplam_musteri;
END //

DELIMITER ;

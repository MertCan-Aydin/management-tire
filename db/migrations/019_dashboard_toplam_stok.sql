-- =============================================
-- 019 — Dashboard'a toplam lastik adedi eklendi
-- =============================================

USE DijitalLastikServisiDB;

DELIMITER //

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
        -- Toplam lastik adedi
        (SELECT COALESCE(SUM(stok), 0) FROM urunler WHERE silindi_mi = 0 AND fiziksel_urun_mu = 1) AS toplam_lastik_adedi,
        -- Toplam müşteri
        (SELECT COUNT(*) FROM musteriler WHERE silindi_mi = 0) AS toplam_musteri;
END //

DELIMITER ;

-- =============================================
-- 006 — RAPOR STORED PROCEDURE'LERİ
-- =============================================

USE DijitalLastikServisiDB;

DELIMITER //

-- Günlük rapor
CREATE PROCEDURE sp_rapor_gunluk(IN p_tarih DATE)
BEGIN
    DECLARE v_baslangic DATETIME;
    DECLARE v_bitis DATETIME;
    SET v_baslangic = CONCAT(p_tarih, ' 00:00:00');
    SET v_bitis    = CONCAT(p_tarih, ' 23:59:59');

    SELECT
        -- Satış özeti
        (SELECT COUNT(*) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0) AS satis_adedi,
        (SELECT COALESCE(SUM(toplam_tutar - indirim), 0) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0) AS toplam_ciro,
        (SELECT COALESCE(SUM(toplam_tutar - indirim - toplam_maliyet), 0) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0) AS toplam_kar,
        -- Ödeme yöntemi dağılımı
        (SELECT COALESCE(SUM(toplam_tutar - indirim), 0) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0 AND odeme_yontemi = 'Nakit') AS nakit_ciro,
        (SELECT COALESCE(SUM(toplam_tutar - indirim), 0) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0 AND odeme_yontemi = 'Kredi Kartı') AS kart_ciro,
        (SELECT COALESCE(SUM(toplam_tutar - indirim), 0) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0 AND odeme_yontemi = 'Havale') AS havale_ciro,
        -- Gider
        (SELECT COALESCE(SUM(tutar), 0) FROM giderler WHERE tarih BETWEEN v_baslangic AND v_bitis) AS toplam_gider,
        -- Net
        (SELECT COALESCE(SUM(toplam_tutar - indirim - toplam_maliyet), 0) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0)
        - (SELECT COALESCE(SUM(tutar), 0) FROM giderler WHERE tarih BETWEEN v_baslangic AND v_bitis) AS net_kar;
END //

-- Tarih aralığı raporu (haftalık/aylık aynı SP kullanılır)
CREATE PROCEDURE sp_rapor_aralik(IN p_baslangic DATE, IN p_bitis DATE)
BEGIN
    DECLARE v_baslangic DATETIME;
    DECLARE v_bitis DATETIME;
    SET v_baslangic = CONCAT(p_baslangic, ' 00:00:00');
    SET v_bitis    = CONCAT(p_bitis, ' 23:59:59');

    SELECT
        (SELECT COUNT(*) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0) AS satis_adedi,
        (SELECT COALESCE(SUM(toplam_tutar - indirim), 0) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0) AS toplam_ciro,
        (SELECT COALESCE(SUM(toplam_tutar - indirim - toplam_maliyet), 0) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0) AS toplam_kar,
        (SELECT COALESCE(SUM(toplam_tutar - indirim), 0) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0 AND odeme_yontemi = 'Nakit') AS nakit_ciro,
        (SELECT COALESCE(SUM(toplam_tutar - indirim), 0) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0 AND odeme_yontemi = 'Kredi Kartı') AS kart_ciro,
        (SELECT COALESCE(SUM(toplam_tutar - indirim), 0) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0 AND odeme_yontemi = 'Havale') AS havale_ciro,
        (SELECT COALESCE(SUM(tutar), 0) FROM giderler WHERE tarih BETWEEN v_baslangic AND v_bitis) AS toplam_gider,
        (SELECT COALESCE(SUM(tutar), 0) FROM tedarikci_odemeleri WHERE tarih BETWEEN v_baslangic AND v_bitis) AS tedarikci_odeme_toplami,
        (SELECT COALESCE(SUM(toplam_tutar - indirim - toplam_maliyet), 0) FROM satislar WHERE tarih BETWEEN v_baslangic AND v_bitis AND iptal_mi = 0)
        - (SELECT COALESCE(SUM(tutar), 0) FROM giderler WHERE tarih BETWEEN v_baslangic AND v_bitis) AS net_kar;
END //

-- Günlük satış kırılımı (aralık içindeki her günün özeti)
CREATE PROCEDURE sp_rapor_gunluk_kirilim(IN p_baslangic DATE, IN p_bitis DATE)
BEGIN
    SELECT
        DATE(s.tarih) AS gun,
        COUNT(*) AS satis_adedi,
        COALESCE(SUM(s.toplam_tutar - s.indirim), 0) AS ciro,
        COALESCE(SUM(s.toplam_tutar - s.indirim - s.toplam_maliyet), 0) AS kar
    FROM satislar s
    WHERE DATE(s.tarih) BETWEEN p_baslangic AND p_bitis AND s.iptal_mi = 0
    GROUP BY DATE(s.tarih)
    ORDER BY gun;
END //

-- En çok satan ürünler
CREATE PROCEDURE sp_rapor_en_cok_satan(IN p_baslangic DATE, IN p_bitis DATE, IN p_limit INT)
BEGIN
    SELECT
        sk.urun_id,
        sk.urun_adi_anlik,
        SUM(sk.miktar) AS toplam_adet,
        SUM(sk.miktar * sk.birim_fiyat) AS toplam_ciro,
        SUM(sk.miktar * (sk.birim_fiyat - sk.birim_maliyet)) AS toplam_kar
    FROM satis_kalemleri sk
    JOIN satislar s ON s.id = sk.satis_id
    WHERE DATE(s.tarih) BETWEEN p_baslangic AND p_bitis AND s.iptal_mi = 0 AND sk.iptal_mi = 0
    GROUP BY sk.urun_id, sk.urun_adi_anlik
    ORDER BY toplam_adet DESC
    LIMIT p_limit;
END //

-- Dashboard özeti (anlık)
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
        (SELECT COUNT(*) FROM musteriler) AS toplam_musteri;
END //

-- Tedarikçi bazlı alım özeti
CREATE PROCEDURE sp_rapor_tedarikci_alim(IN p_baslangic DATE, IN p_bitis DATE)
BEGIN
    SELECT
        t.id, t.ad AS tedarikci_adi,
        COUNT(a.id) AS alim_sayisi,
        COALESCE(SUM(a.toplam_tutar), 0) AS toplam_alim,
        t.guncel_borc
    FROM tedarikciler t
    LEFT JOIN alimlar a ON a.tedarikci_id = t.id
        AND DATE(a.tarih) BETWEEN p_baslangic AND p_bitis
        AND a.iptal_mi = 0
    WHERE t.silindi_mi = 0
    GROUP BY t.id, t.ad, t.guncel_borc
    ORDER BY toplam_alim DESC;
END //

DELIMITER ;

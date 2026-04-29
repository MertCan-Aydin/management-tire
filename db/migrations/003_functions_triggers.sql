-- =============================================
-- 003 — FONKSİYONLAR VE TETİKLEYİCİLER
-- =============================================

USE DijitalLastikServisiDB;

-- ###############################################
-- KULLANICI TANIMLI FONKSİYONLAR
-- ###############################################

DELIMITER //

CREATE FUNCTION fn_urun_stok_durumu(p_urun_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE v_stok INT;
    SELECT stok INTO v_stok FROM urunler WHERE id = p_urun_id;
    RETURN IFNULL(v_stok, 0);
END //

CREATE FUNCTION fn_satis_kari_hesapla(p_satis_id INT)
RETURNS DECIMAL(18,2)
DETERMINISTIC
BEGIN
    DECLARE v_tutar DECIMAL(18,2);
    DECLARE v_maliyet DECIMAL(18,2);
    DECLARE v_indirim DECIMAL(18,2);
    SELECT toplam_tutar, toplam_maliyet, indirim INTO v_tutar, v_maliyet, v_indirim FROM satislar WHERE id = p_satis_id;
    RETURN IFNULL((v_tutar - v_indirim) - v_maliyet, 0.00);
END //

DELIMITER ;

-- ###############################################
-- TETİKLEYİCİLER
-- ###############################################

DELIMITER //

-- Satış kalemi eklendiğinde: stok düş, satış toplamlarını güncelle
CREATE TRIGGER trg_satis_kalemi_eklendikten_sonra
AFTER INSERT ON satis_kalemleri
FOR EACH ROW
BEGIN
    DECLARE v_fiziksel_mi BOOLEAN;
    SELECT fiziksel_urun_mu INTO v_fiziksel_mi FROM urunler WHERE id = NEW.urun_id;
    IF v_fiziksel_mi = 1 THEN
        UPDATE urunler SET stok = stok - NEW.miktar WHERE id = NEW.urun_id;
    END IF;
    UPDATE satislar
    SET toplam_tutar = toplam_tutar + (NEW.miktar * NEW.birim_fiyat),
        toplam_maliyet = toplam_maliyet + (NEW.miktar * NEW.birim_maliyet)
    WHERE id = NEW.satis_id;
END //

-- Alım kalemi eklendiğinde: stok artır, alım toplamını güncelle, tedarikçi borcunu artır
CREATE TRIGGER trg_alim_kalemi_eklendikten_sonra
AFTER INSERT ON alim_kalemleri
FOR EACH ROW
BEGIN
    DECLARE v_fiziksel_mi BOOLEAN;
    DECLARE v_tedarikci_id INT;
    DECLARE v_kalem_tutari DECIMAL(18,2);
    SET v_kalem_tutari = NEW.miktar * NEW.birim_fiyat;
    SELECT fiziksel_urun_mu INTO v_fiziksel_mi FROM urunler WHERE id = NEW.urun_id;
    IF v_fiziksel_mi = 1 THEN
        UPDATE urunler SET stok = stok + NEW.miktar WHERE id = NEW.urun_id;
    END IF;
    UPDATE alimlar SET toplam_tutar = toplam_tutar + v_kalem_tutari WHERE id = NEW.alim_id;
    SELECT tedarikci_id INTO v_tedarikci_id FROM alimlar WHERE id = NEW.alim_id;
    UPDATE tedarikciler SET guncel_borc = guncel_borc + v_kalem_tutari WHERE id = v_tedarikci_id;
END //

-- Tedarikçiye ödeme yapıldığında: borcu düşür
CREATE TRIGGER trg_tedarikciye_odeme_yapildiginda
AFTER INSERT ON tedarikci_odemeleri
FOR EACH ROW
BEGIN
    UPDATE tedarikciler SET guncel_borc = guncel_borc - NEW.tutar WHERE id = NEW.tedarikci_id;
END //

DELIMITER ;

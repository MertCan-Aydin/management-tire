-- ─────────────────────────────────────────────────────────────────────────────
-- 012_alim_iptal.sql  —  Alım iptali (stok ve tedarikçi borcu geri alınır)
-- ─────────────────────────────────────────────────────────────────────────────
-- Eski sp_alimlar_sil kaydı DELETE ile kaldırmaya çalışıyordu: kalemi olan
-- alımda alim_kalemleri yabancı anahtarı yüzünden hata veriyor, çalışsa bile
-- trg_alim_kalemi_eklendikten_sonra'nın artırdığı stok ve tedarikçi borcunu
-- geri almıyordu.
--
-- Artık alım silinmez, iptal_mi = 1 yapılır (satış iptaliyle aynı):
--   * Fiziksel ürünlerin stoğu alınan miktar kadar düşülür.
--   * Tedarikçinin guncel_borc'u alım tutarı kadar azaltılır. Alım zaten
--     ödendiyse borç eksiye düşer; bu tedarikçiden alacak demektir.
--   * Ürünlerin bir kısmı satıldığı için stok yetmiyorsa iptal reddedilir.
--   * Zaten iptal edilmiş alım ikinci kez iptal edilemez.
--
-- KULLANIM (admin yetkisiyle; lastik_user CREATE PROCEDURE yapamaz):
--     sudo mysql DijitalLastikServisiDB < 012_alim_iptal.sql
-- ─────────────────────────────────────────────────────────────────────────────

DELIMITER //

DROP PROCEDURE IF EXISTS sp_alimlar_sil //
CREATE PROCEDURE sp_alimlar_sil(IN p_id INT)
BEGIN
    DECLARE v_iptal_mi     BOOLEAN;
    DECLARE v_tedarikci_id INT;
    DECLARE v_tutar        DECIMAL(18,2);
    DECLARE v_kilitli      INT;
    DECLARE v_eksik_urun   VARCHAR(100) DEFAULT NULL;
    DECLARE v_mesaj        VARCHAR(128);

    SELECT iptal_mi, tedarikci_id, toplam_tutar
    INTO v_iptal_mi, v_tedarikci_id, v_tutar
    FROM alimlar WHERE id = p_id
    FOR UPDATE;

    IF v_tedarikci_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Alım bulunamadı';
    END IF;

    IF v_iptal_mi = 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Bu alım zaten iptal edilmiş';
    END IF;

    -- Stok satırlarını kilitle ki kontrol ile düşüm arasında satış araya girmesin.
    SELECT COUNT(*) INTO v_kilitli
    FROM urunler
    WHERE id IN (SELECT urun_id FROM alim_kalemleri WHERE alim_id = p_id)
    FOR UPDATE;

    -- Aynı ürün birden fazla kalemde olabilir; ürün başına toplam miktarla karşılaştır.
    SELECT LEFT(k.urun_adi, 60) INTO v_eksik_urun
    FROM (
        SELECT urun_id, SUM(miktar) AS miktar, MAX(urun_adi_anlik) AS urun_adi
        FROM alim_kalemleri WHERE alim_id = p_id
        GROUP BY urun_id
    ) k
    JOIN urunler u ON u.id = k.urun_id
    WHERE u.fiziksel_urun_mu = 1 AND u.stok < k.miktar
    LIMIT 1;

    IF v_eksik_urun IS NOT NULL THEN
        SET v_mesaj = CONCAT('Stok yetersiz: "', v_eksik_urun, '" satılmış, alım iptal edilemez');
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_mesaj;
    END IF;

    UPDATE urunler u
    JOIN (
        SELECT urun_id, SUM(miktar) AS miktar
        FROM alim_kalemleri WHERE alim_id = p_id
        GROUP BY urun_id
    ) k ON k.urun_id = u.id
    SET u.stok = u.stok - k.miktar
    WHERE u.fiziksel_urun_mu = 1;

    UPDATE tedarikciler SET guncel_borc = guncel_borc - v_tutar WHERE id = v_tedarikci_id;

    UPDATE alimlar SET iptal_mi = 1 WHERE id = p_id;
END //

DELIMITER ;

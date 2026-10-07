-- ─────────────────────────────────────────────────────────────────────────────
-- 013_satis_iptal.sql  —  Satış iptalinde stoğu geri ekleme seçeneği
-- ─────────────────────────────────────────────────────────────────────────────
-- Eski sp_satislar_sil yalnızca iptal_mi = 1 yapıyordu; trg_satis_kalemi_
-- eklendikten_sonra'nın düştüğü stok hiç geri eklenmiyordu.
--
-- Artık iptal eden kişi seçer (p_stoga_ekle):
--   * 1 → Fiziksel ürünler satılan miktar kadar stoğa geri eklenir
--         (ürün kullanılmadan iptal edildiyse — en sık durum).
--   * 0 → Stoğa dokunulmaz (ürün takıldı / hasarlı iade, tekrar satılamaz).
--   * Zaten iptal edilmiş satış ikinci kez iptal edilemez; aksi halde stok
--     iki kez eklenirdi.
--
-- İmza değiştiği için API ile birlikte uygulanmalı: önce bu dosya, hemen
-- ardından deploy.sh (arada eski API satış iptal ederse hata alır).
--
-- KULLANIM (admin yetkisiyle; lastik_user CREATE PROCEDURE yapamaz):
--     sudo mysql DijitalLastikServisiDB < 013_satis_iptal.sql
-- ─────────────────────────────────────────────────────────────────────────────

DELIMITER //

DROP PROCEDURE IF EXISTS sp_satislar_sil //
CREATE PROCEDURE sp_satislar_sil(IN p_id INT, IN p_stoga_ekle BOOLEAN)
BEGIN
    DECLARE v_iptal_mi BOOLEAN DEFAULT NULL;

    SELECT iptal_mi INTO v_iptal_mi
    FROM satislar WHERE id = p_id
    FOR UPDATE;

    IF v_iptal_mi IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Satış bulunamadı';
    END IF;

    IF v_iptal_mi = 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Bu satış zaten iptal edilmiş';
    END IF;

    IF p_stoga_ekle THEN
        UPDATE urunler u
        JOIN (
            SELECT urun_id, SUM(miktar) AS miktar
            FROM satis_kalemleri
            WHERE satis_id = p_id AND iptal_mi = 0
            GROUP BY urun_id
        ) k ON k.urun_id = u.id
        SET u.stok = u.stok + k.miktar
        WHERE u.fiziksel_urun_mu = 1;
    END IF;

    UPDATE satislar SET iptal_mi = 1 WHERE id = p_id;
END //

-- Kalem iptali hiçbir istemcide kullanılmıyordu ve satış toplamı, kâr ve
-- stoğu düzeltmiyordu; API ucu kaldırıldı, SP de kaldırılır.
DROP PROCEDURE IF EXISTS sp_satis_kalemleri_sil //

DELIMITER ;

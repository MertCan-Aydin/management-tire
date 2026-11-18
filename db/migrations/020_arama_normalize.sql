-- =============================================
-- 020 — Aramada / olmadan ebat aranabilsin
-- =============================================

USE DijitalLastikServisiDB;

DROP PROCEDURE IF EXISTS sp_urunler_listele;
DELIMITER //
CREATE PROCEDURE sp_urunler_listele(
    IN p_arama VARCHAR(100),
    IN p_urun_tipi_id INT,
    IN p_marka_id INT,
    IN p_sadece_stoklu BOOLEAN,
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    DECLARE v_arama VARCHAR(100);
    SET v_arama = REPLACE(REPLACE(p_arama, ' ', ''), '/', '');

    SELECT
        u.id, u.barkod_qr, u.ad, u.ebat,
        u.yuk_indeksi, u.hiz_kodu, u.ekstra_yuk, u.uretim_yili,
        u.satis_fiyati, u.maliyet_fiyati,
        u.maliyet_bilinmiyor, u.guncel_borctan,
        u.stok, u.fiziksel_urun_mu,
        u.resim_yolu, u.silindi_mi,
        u.urun_tipi_id, u.marka_id, u.marka_modeli_id,
        t.ad AS tip_adi, m.ad AS marka_adi, mm.ad AS model_adi, mm.mevsim
    FROM urunler u
    JOIN urun_tipleri t ON t.id = u.urun_tipi_id
    JOIN urun_markalari m ON m.id = u.marka_id
    JOIN urun_marka_modelleri mm ON mm.id = u.marka_modeli_id
    WHERE
        u.silindi_mi = 0
        AND (p_arama IS NULL OR p_arama = ''
            OR u.ad LIKE CONCAT('%', p_arama, '%')
            OR u.barkod_qr = p_arama
            OR u.ebat LIKE CONCAT('%', p_arama, '%')
            OR REPLACE(REPLACE(u.ebat, ' ', ''), '/', '') LIKE CONCAT('%', v_arama, '%')
            OR REPLACE(REPLACE(u.ad, ' ', ''), '/', '') LIKE CONCAT('%', v_arama, '%')
        )
        AND (p_urun_tipi_id IS NULL OR u.urun_tipi_id = p_urun_tipi_id)
        AND (p_marka_id IS NULL OR u.marka_id = p_marka_id)
        AND (p_sadece_stoklu = 0 OR u.stok > 0)
    ORDER BY u.ad
    LIMIT p_limit OFFSET p_offset;
END //
DELIMITER ;

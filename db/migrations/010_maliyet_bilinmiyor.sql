-- Ürünlere "alış fiyatı bilinmiyor" ve "güncel borçtan" alanları ekle
ALTER TABLE urunler
    ADD COLUMN maliyet_bilinmiyor TINYINT(1) NOT NULL DEFAULT 0 AFTER maliyet_fiyati,
    ADD COLUMN guncel_borctan TINYINT(1) NOT NULL DEFAULT 0 AFTER maliyet_bilinmiyor;

-- sp_urunler_ekle: iki yeni parametre
DROP PROCEDURE IF EXISTS sp_urunler_ekle;
DELIMITER //
CREATE PROCEDURE sp_urunler_ekle(
    IN p_barkod_qr VARCHAR(100),
    IN p_ad VARCHAR(100),
    IN p_ebat VARCHAR(50),
    IN p_aciklama TEXT,
    IN p_satis_fiyati DECIMAL(18,2),
    IN p_maliyet_fiyati DECIMAL(18,2),
    IN p_maliyet_bilinmiyor BOOLEAN,
    IN p_guncel_borctan BOOLEAN,
    IN p_stok INT,
    IN p_fiziksel_urun_mu BOOLEAN,
    IN p_resim_yolu VARCHAR(255),
    IN p_urun_tipi_id INT,
    IN p_marka_id INT,
    IN p_marka_modeli_id INT
)
BEGIN
    INSERT INTO urunler (
        barkod_qr, ad, ebat, aciklama, satis_fiyati,
        maliyet_fiyati, maliyet_bilinmiyor, guncel_borctan,
        stok, fiziksel_urun_mu, resim_yolu,
        urun_tipi_id, marka_id, marka_modeli_id
    ) VALUES (
        p_barkod_qr, p_ad, p_ebat, p_aciklama, p_satis_fiyati,
        p_maliyet_fiyati, p_maliyet_bilinmiyor, p_guncel_borctan,
        p_stok, p_fiziksel_urun_mu, p_resim_yolu,
        p_urun_tipi_id, p_marka_id, p_marka_modeli_id
    );
    SELECT LAST_INSERT_ID() AS id;
END //
DELIMITER ;

-- sp_urunler_guncelle: iki yeni parametre
DROP PROCEDURE IF EXISTS sp_urunler_guncelle;
DELIMITER //
CREATE PROCEDURE sp_urunler_guncelle(
    IN p_id INT,
    IN p_barkod_qr VARCHAR(100),
    IN p_ad VARCHAR(100),
    IN p_ebat VARCHAR(50),
    IN p_aciklama TEXT,
    IN p_satis_fiyati DECIMAL(18,2),
    IN p_maliyet_fiyati DECIMAL(18,2),
    IN p_maliyet_bilinmiyor BOOLEAN,
    IN p_guncel_borctan BOOLEAN,
    IN p_stok INT,
    IN p_fiziksel_urun_mu BOOLEAN,
    IN p_resim_yolu VARCHAR(255),
    IN p_silindi_mi BOOLEAN,
    IN p_urun_tipi_id INT,
    IN p_marka_id INT,
    IN p_marka_modeli_id INT
)
BEGIN
    UPDATE urunler SET
        barkod_qr = p_barkod_qr,
        ad = p_ad,
        ebat = p_ebat,
        aciklama = p_aciklama,
        satis_fiyati = p_satis_fiyati,
        maliyet_fiyati = p_maliyet_fiyati,
        maliyet_bilinmiyor = p_maliyet_bilinmiyor,
        guncel_borctan = p_guncel_borctan,
        stok = p_stok,
        fiziksel_urun_mu = p_fiziksel_urun_mu,
        resim_yolu = p_resim_yolu,
        silindi_mi = p_silindi_mi,
        urun_tipi_id = p_urun_tipi_id,
        marka_id = p_marka_id,
        marka_modeli_id = p_marka_modeli_id
    WHERE id = p_id;
END //
DELIMITER ;

-- sp_urunler_getir: yeni alanları da döndür
DROP PROCEDURE IF EXISTS sp_urunler_getir;
DELIMITER //
CREATE PROCEDURE sp_urunler_getir(IN p_id INT)
BEGIN
    SELECT
        u.id, u.barkod_qr, u.ad, u.ebat, u.aciklama,
        u.satis_fiyati, u.maliyet_fiyati, u.maliyet_bilinmiyor, u.guncel_borctan,
        u.stok, u.fiziksel_urun_mu,
        u.resim_yolu, u.silindi_mi,
        u.urun_tipi_id, u.marka_id, u.marka_modeli_id,
        t.ad AS tip_adi, m.ad AS marka_adi, mm.ad AS model_adi, mm.mevsim
    FROM urunler u
    JOIN urun_tipleri t ON t.id = u.urun_tipi_id
    JOIN urun_markalari m ON m.id = u.marka_id
    JOIN urun_marka_modelleri mm ON mm.id = u.marka_modeli_id
    WHERE u.id = p_id;
END //
DELIMITER ;

-- sp_urunler_listele: yeni alanları da döndür
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
    SELECT
        u.id, u.barkod_qr, u.ad, u.ebat, u.satis_fiyati,
        u.maliyet_fiyati, u.maliyet_bilinmiyor, u.guncel_borctan,
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
        AND (p_arama IS NULL OR u.ad LIKE CONCAT('%', p_arama, '%') OR u.barkod_qr = p_arama OR u.ebat LIKE CONCAT('%', p_arama, '%'))
        AND (p_urun_tipi_id IS NULL OR u.urun_tipi_id = p_urun_tipi_id)
        AND (p_marka_id IS NULL OR u.marka_id = p_marka_id)
        AND (p_sadece_stoklu = 0 OR u.stok > 0)
    ORDER BY u.ad
    LIMIT p_limit OFFSET p_offset;
END //
DELIMITER ;

-- sp_urunler_barkod_ara: yeni alanları da döndür
DROP PROCEDURE IF EXISTS sp_urunler_barkod_ara;
DELIMITER //
CREATE PROCEDURE sp_urunler_barkod_ara(IN p_barkod VARCHAR(100))
BEGIN
    SELECT
        u.id, u.barkod_qr, u.ad, u.ebat,
        u.satis_fiyati, u.maliyet_fiyati, u.maliyet_bilinmiyor, u.guncel_borctan,
        u.stok, u.fiziksel_urun_mu,
        u.urun_tipi_id, u.marka_id, u.marka_modeli_id,
        t.ad AS tip_adi, m.ad AS marka_adi, mm.ad AS model_adi, mm.mevsim
    FROM urunler u
    JOIN urun_tipleri t ON t.id = u.urun_tipi_id
    JOIN urun_markalari m ON m.id = u.marka_id
    JOIN urun_marka_modelleri mm ON mm.id = u.marka_modeli_id
    WHERE u.barkod_qr = p_barkod AND u.silindi_mi = 0;
END //
DELIMITER ;

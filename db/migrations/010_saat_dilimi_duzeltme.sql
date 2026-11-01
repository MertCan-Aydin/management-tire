-- =============================================================================
-- 010_saat_dilimi_duzeltme.sql  —  TEK SEFERLİK veri düzeltmesi
-- =============================================================================
-- Sunucu UTC'deyken DEFAULT CURRENT_TIMESTAMP ile yazılan tarihler Türkiye
-- saatinden 3 saat geride kaldı. a98d82e commit'inden (DB bağlantısında
-- time_zone = '+03:00') sonra yeni kayıtlar doğru yazılıyor; bu betik ESKİ
-- kayıtları 3 saat ileri alır.
--
-- YALNIZCA sunucu saat dilimi UTC idiyse çalıştırın:
--     timedatectl                                   →  Time zone: Etc/UTC
--     sudo mysql -e "SELECT @@global.time_zone, @@system_time_zone"
--                                                   →  SYSTEM | UTC
--
-- KESİM ZAMANI: API'nin yeni kodla yeniden başlatıldığı an, UTC olarak.
--     systemctl show management-tire-api -p ActiveEnterTimestamp
-- Bu andan önceki kayıtlar UTC, sonrakiler Türkiye saatiyle yazıldı. Yeni
-- kayıtların değeri her zaman kesim + 3 saatten büyük olduğu için ayrım
-- kesin; kesimi birkaç dakika geç vermek sorun olmaz, erken vermeyin.
--
-- KULLANIM (admin yetkisiyle; lastik_user CREATE PROCEDURE yapamaz):
--     1) Yedek:   sudo mysqldump DijitalLastikServisiDB > yedek_$(date +%F_%H%M).sql
--     2) Aşağıdaki @kesim değerini girin, @uygula = 0 bırakın, çalıştırın:
--                 sudo mysql DijitalLastikServisiDB < 010_saat_dilimi_duzeltme.sql
--        → Hangi tablodan kaç kaydın kaydırılacağını gösterir, hiçbir şey değişmez.
--     3) Sayılar mantıklıysa @uygula = 1 yapıp tekrar çalıştırın.
--
-- Betik ikinci kez uygulanamaz (bakim_islemleri tablosundaki kayıt engeller).
-- Kullanıcının elle seçtiği tarihlere (lastik oteli giriş/çıkış) dokunulmaz.
-- =============================================================================

SET @kesim  = NULL;   -- ← ör. '2026-10-07 09:15:00' — API'nin yeniden başladığı an (UTC)
SET @uygula = 0;                       -- ← 0 = önizleme, 1 = uygula

CREATE TABLE IF NOT EXISTS bakim_islemleri (
    ad          VARCHAR(100) PRIMARY KEY,
    uygulandi   DATETIME     NOT NULL,
    aciklama    TEXT
);

DROP PROCEDURE IF EXISTS sp_bakim_saat_dilimi_duzelt;

DELIMITER //

CREATE PROCEDURE sp_bakim_saat_dilimi_duzelt(IN p_kesim DATETIME, IN p_uygula BOOLEAN)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    IF EXISTS (SELECT 1 FROM bakim_islemleri WHERE ad = 'saat_dilimi_utc_to_tr') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Bu düzeltme daha önce uygulanmış. İkinci kez çalıştırmak saatleri 6 saat kaydırır.';
    END IF;

    IF p_kesim IS NULL OR p_kesim > UTC_TIMESTAMP() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Kesim zamanı boş ya da gelecekte. @kesim değerini kontrol edin.';
    END IF;

    SELECT 'satislar'            AS tablo, COUNT(*) AS kaydirilacak, MIN(tarih) AS en_eski, MAX(tarih) AS en_yeni FROM satislar            WHERE tarih < p_kesim
    UNION ALL SELECT 'alimlar',             COUNT(*), MIN(tarih), MAX(tarih) FROM alimlar             WHERE tarih < p_kesim
    UNION ALL SELECT 'giderler',            COUNT(*), MIN(tarih), MAX(tarih) FROM giderler            WHERE tarih < p_kesim
    UNION ALL SELECT 'tedarikci_odemeleri', COUNT(*), MIN(tarih), MAX(tarih) FROM tedarikci_odemeleri WHERE tarih < p_kesim
    UNION ALL SELECT 'iptal_kayitlari',     COUNT(*), MIN(tarih), MAX(tarih) FROM iptal_kayitlari     WHERE tarih < p_kesim
    UNION ALL SELECT 'urun_partileri',      COUNT(*), MIN(eklenme_tarihi), MAX(eklenme_tarihi) FROM urun_partileri WHERE eklenme_tarihi < p_kesim
    UNION ALL SELECT 'lastik_oteli',        COUNT(*), MIN(olusturulma_tarihi), MAX(olusturulma_tarihi) FROM lastik_oteli WHERE olusturulma_tarihi < p_kesim;

    IF p_uygula THEN
        START TRANSACTION;

        UPDATE satislar            SET tarih = tarih + INTERVAL 3 HOUR WHERE tarih < p_kesim;
        UPDATE alimlar             SET tarih = tarih + INTERVAL 3 HOUR WHERE tarih < p_kesim;
        UPDATE giderler            SET tarih = tarih + INTERVAL 3 HOUR WHERE tarih < p_kesim;
        UPDATE tedarikci_odemeleri SET tarih = tarih + INTERVAL 3 HOUR WHERE tarih < p_kesim;
        UPDATE iptal_kayitlari     SET tarih = tarih + INTERVAL 3 HOUR WHERE tarih < p_kesim;
        UPDATE urun_partileri      SET eklenme_tarihi = eklenme_tarihi + INTERVAL 3 HOUR WHERE eklenme_tarihi < p_kesim;
        UPDATE lastik_oteli        SET olusturulma_tarihi = olusturulma_tarihi + INTERVAL 3 HOUR WHERE olusturulma_tarihi < p_kesim;

        INSERT INTO bakim_islemleri (ad, uygulandi, aciklama)
        VALUES ('saat_dilimi_utc_to_tr', UTC_TIMESTAMP(), CONCAT('Kesim (UTC): ', p_kesim, ' — kayıtlar +3 saat kaydırıldı'));

        COMMIT;
        SELECT 'UYGULANDI — kayıtlar 3 saat ileri alındı.' AS sonuc;
    ELSE
        SELECT 'ÖNİZLEME — hiçbir kayıt değişmedi. Uygulamak için @uygula = 1 yapın.' AS sonuc;
    END IF;
END //

DELIMITER ;

CALL sp_bakim_saat_dilimi_duzelt(@kesim, @uygula);

DROP PROCEDURE IF EXISTS sp_bakim_saat_dilimi_duzelt;

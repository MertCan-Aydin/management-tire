-- Lastik marka / model / ebat hızlı seçim listeleri
-- Ürün tablosundan bağımsız; alım formunda kolaylaştırma amaçlı.

CREATE TABLE IF NOT EXISTS lastik_markalari (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ad VARCHAR(100) NOT NULL UNIQUE,
    olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS lastik_modelleri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ad VARCHAR(150) NOT NULL UNIQUE,
    olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS lastik_ebatlari (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ebat VARCHAR(50) NOT NULL,
    kategori ENUM('Otomobil','Kamyon','TIR') NOT NULL DEFAULT 'Otomobil',
    olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_ebat_kategori (ebat, kategori)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ═══ Stored Procedures ═══

DELIMITER //

-- Markalar
DROP PROCEDURE IF EXISTS sp_lastik_markalari_listele//
CREATE PROCEDURE sp_lastik_markalari_listele()
BEGIN
    SELECT id, ad FROM lastik_markalari ORDER BY ad;
END//

DROP PROCEDURE IF EXISTS sp_lastik_markalari_ekle//
CREATE PROCEDURE sp_lastik_markalari_ekle(IN p_ad VARCHAR(100))
BEGIN
    INSERT IGNORE INTO lastik_markalari (ad) VALUES (p_ad);
    SELECT LAST_INSERT_ID() AS id;
END//

-- Modeller
DROP PROCEDURE IF EXISTS sp_lastik_modelleri_listele//
CREATE PROCEDURE sp_lastik_modelleri_listele()
BEGIN
    SELECT id, ad FROM lastik_modelleri ORDER BY ad;
END//

DROP PROCEDURE IF EXISTS sp_lastik_modelleri_ekle//
CREATE PROCEDURE sp_lastik_modelleri_ekle(IN p_ad VARCHAR(150))
BEGIN
    INSERT IGNORE INTO lastik_modelleri (ad) VALUES (p_ad);
    SELECT LAST_INSERT_ID() AS id;
END//

-- Ebatlar
DROP PROCEDURE IF EXISTS sp_lastik_ebatlari_listele//
CREATE PROCEDURE sp_lastik_ebatlari_listele(IN p_kategori VARCHAR(20))
BEGIN
    IF p_kategori IS NULL OR p_kategori = '' THEN
        SELECT id, ebat, kategori FROM lastik_ebatlari ORDER BY kategori, ebat;
    ELSE
        SELECT id, ebat, kategori FROM lastik_ebatlari WHERE kategori = p_kategori ORDER BY ebat;
    END IF;
END//

DROP PROCEDURE IF EXISTS sp_lastik_ebatlari_ekle//
CREATE PROCEDURE sp_lastik_ebatlari_ekle(IN p_ebat VARCHAR(50), IN p_kategori VARCHAR(20))
BEGIN
    INSERT IGNORE INTO lastik_ebatlari (ebat, kategori) VALUES (p_ebat, p_kategori);
    SELECT LAST_INSERT_ID() AS id;
END//

DELIMITER ;

-- ═══ Varsayılan Veriler ═══

-- Markalar (30)
INSERT IGNORE INTO lastik_markalari (ad) VALUES
('Michelin'),('Continental'),('Bridgestone'),('Pirelli'),('Goodyear'),
('Dunlop'),('Hankook'),('Yokohama'),('Firestone'),('Toyo'),
('Kumho'),('Nexen'),('Falken'),('Cooper'),('Maxxis'),
('Lassa'),('Petlas'),('Nankang'),('GT Radial'),('Sailun'),
('Linglong'),('Triangle'),('Westlake'),('Federal'),('Vredestein'),
('BFGoodrich'),('Nokian'),('Semperit'),('Uniroyal'),('Kormoran');

-- Modeller (30)
INSERT IGNORE INTO lastik_modelleri (ad) VALUES
('Primacy 4+'),('Pilot Sport 5'),('CrossClimate 2'),('Alpin 6'),
('PremiumContact 6'),('EcoContact 6'),('WinterContact TS 870'),('AllSeasonContact'),
('Turanza T005'),('Blizzak LM005'),('Potenza Sport'),('Ecopia EP150'),
('Cinturato P7'),('P Zero'),('Winter Sottozero 3'),('Scorpion Verde'),
('EfficientGrip Performance 2'),('UltraGrip 9+'),('Vector 4Seasons Gen-3'),
('Ventus Prime 4'),('Winter i*cept RS3'),('Kinergy Eco 2'),
('BluEarth-GT AE51'),('W.drive V905'),
('Snowprox S944'),('Proxes Sport'),('Competus A/T3'),
('Drivepoint 3'),('Snowmaster W651'),('Adreno A/T');

-- Otomobil ebatları (30)
INSERT IGNORE INTO lastik_ebatlari (ebat, kategori) VALUES
('155/65R14','Otomobil'),('165/65R14','Otomobil'),('165/70R14','Otomobil'),
('175/65R14','Otomobil'),('175/70R14','Otomobil'),
('185/55R15','Otomobil'),('185/60R15','Otomobil'),('185/65R14','Otomobil'),
('185/65R15','Otomobil'),('185/70R14','Otomobil'),
('195/55R16','Otomobil'),('195/60R15','Otomobil'),('195/65R15','Otomobil'),('195/70R14','Otomobil'),
('205/55R16','Otomobil'),('205/60R15','Otomobil'),('205/60R16','Otomobil'),('205/65R15','Otomobil'),
('215/55R16','Otomobil'),('215/55R17','Otomobil'),('215/60R16','Otomobil'),('215/65R16','Otomobil'),
('225/40R18','Otomobil'),('225/45R17','Otomobil'),('225/45R18','Otomobil'),
('225/50R17','Otomobil'),('225/55R17','Otomobil'),
('235/40R18','Otomobil'),('235/45R17','Otomobil'),('235/55R17','Otomobil');

-- Kamyon ebatları (30)
INSERT IGNORE INTO lastik_ebatlari (ebat, kategori) VALUES
('215/75R17.5','Kamyon'),('225/75R17.5','Kamyon'),('235/75R17.5','Kamyon'),
('245/70R17.5','Kamyon'),('245/70R19.5','Kamyon'),
('265/70R17.5','Kamyon'),('265/70R19.5','Kamyon'),
('275/70R22.5','Kamyon'),('275/80R22.5','Kamyon'),
('285/70R19.5','Kamyon'),
('295/60R22.5','Kamyon'),('295/80R22.5','Kamyon'),
('305/70R19.5','Kamyon'),('305/70R22.5','Kamyon'),
('315/60R22.5','Kamyon'),('315/70R22.5','Kamyon'),('315/80R22.5','Kamyon'),
('325/95R24','Kamyon'),
('385/55R22.5','Kamyon'),('385/65R22.5','Kamyon'),
('12R22.5','Kamyon'),('13R22.5','Kamyon'),
('7.50R16','Kamyon'),('8.25R16','Kamyon'),
('9.00R20','Kamyon'),('10.00R20','Kamyon'),('11.00R20','Kamyon'),('12.00R20','Kamyon'),
('12.00R24','Kamyon'),('14.00R20','Kamyon');

-- TIR ebatları (30)
INSERT IGNORE INTO lastik_ebatlari (ebat, kategori) VALUES
('315/80R22.5','TIR'),('315/70R22.5','TIR'),('315/60R22.5','TIR'),
('385/65R22.5','TIR'),('385/55R22.5','TIR'),
('295/80R22.5','TIR'),('295/60R22.5','TIR'),
('275/70R22.5','TIR'),('275/80R22.5','TIR'),
('305/70R22.5','TIR'),
('12R22.5','TIR'),('13R22.5','TIR'),('11R22.5','TIR'),
('425/65R22.5','TIR'),('445/45R19.5','TIR'),('445/65R22.5','TIR'),
('455/40R22.5','TIR'),
('215/75R17.5','TIR'),('225/75R17.5','TIR'),('235/75R17.5','TIR'),
('245/70R17.5','TIR'),('245/70R19.5','TIR'),
('265/70R19.5','TIR'),
('285/70R19.5','TIR'),
('305/70R19.5','TIR'),
('325/95R24','TIR'),
('12.00R20','TIR'),('12.00R24','TIR'),('14.00R20','TIR'),('14.00R24','TIR');

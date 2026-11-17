-- ============================================
-- TÜM VERİLERİ SIFIRLA (Yapı + SP korunur)
-- Kullanıcı hesapları ve lastik verileri korunur.
-- ============================================

SET FOREIGN_KEY_CHECKS = 0;

-- Hareket tabloları
TRUNCATE TABLE satis_kalemleri;
TRUNCATE TABLE alim_kalemleri;
TRUNCATE TABLE urun_partileri;
TRUNCATE TABLE satislar;
TRUNCATE TABLE alimlar;
TRUNCATE TABLE tedarikci_odemeleri;
TRUNCATE TABLE tedarikci_kisileri;
TRUNCATE TABLE giderler;
TRUNCATE TABLE lastik_oteli;
TRUNCATE TABLE aktivite_loglari;

-- Ürün hiyerarşisi
TRUNCATE TABLE urunler;
TRUNCATE TABLE urun_marka_modelleri;
TRUNCATE TABLE urun_markalari;
TRUNCATE TABLE urun_tipleri;

-- Müşteriler ve tedarikçiler
TRUNCATE TABLE musteriler;
TRUNCATE TABLE tedarikciler;

-- Oturum tokenları (kullanıcı hesapları korunur)
TRUNCATE TABLE refresh_tokenlar;

-- Lastik seçim listeleri (seed ile yeniden yüklenecek)
TRUNCATE TABLE lastik_markalari;
TRUNCATE TABLE lastik_modelleri;
TRUNCATE TABLE lastik_ebatlari;

SET FOREIGN_KEY_CHECKS = 1;

-- ═══ Lastik seed verilerini yeniden yükle ═══

-- Markalar (30)
INSERT INTO lastik_markalari (ad) VALUES
('Michelin'),('Continental'),('Bridgestone'),('Pirelli'),('Goodyear'),
('Dunlop'),('Hankook'),('Yokohama'),('Firestone'),('Toyo'),
('Kumho'),('Nexen'),('Falken'),('Cooper'),('Maxxis'),
('Lassa'),('Petlas'),('Nankang'),('GT Radial'),('Sailun'),
('Linglong'),('Triangle'),('Westlake'),('Federal'),('Vredestein'),
('BFGoodrich'),('Nokian'),('Semperit'),('Uniroyal'),('Kormoran');

-- Modeller (30)
INSERT INTO lastik_modelleri (ad) VALUES
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
INSERT INTO lastik_ebatlari (ebat, kategori) VALUES
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
INSERT INTO lastik_ebatlari (ebat, kategori) VALUES
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
INSERT INTO lastik_ebatlari (ebat, kategori) VALUES
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

SELECT 'Veriler sıfırlandı. Kullanıcı hesapları ve lastik listeleri korundu.' AS sonuc;

-- =============================================
-- 001 — VERİTABANI VE TABLOLAR
-- =============================================

CREATE DATABASE IF NOT EXISTS DijitalLastikServisiDB
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE DijitalLastikServisiDB;

-- =============================================
-- 1. BAĞIMSIZ TABLOLAR
-- =============================================

CREATE TABLE urun_tipleri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ad VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE tedarikciler (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ad VARCHAR(100) NOT NULL,
    iletisim_bilgisi VARCHAR(255) NULL,
    guncel_borc DECIMAL(18,2) DEFAULT 0.00,
    silindi_mi BOOLEAN DEFAULT 0
);

CREATE TABLE musteriler (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ad_soyad VARCHAR(100) NOT NULL,
    telefon VARCHAR(20) NOT NULL UNIQUE,
    arac_markasi VARCHAR(50) NULL,
    arac_plakasi VARCHAR(20) NULL UNIQUE,
    notlar TEXT NULL
);

CREATE TABLE giderler (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aciklama VARCHAR(255) NOT NULL,
    tutar DECIMAL(18,2) NOT NULL CHECK (tutar > 0),
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- 2. BİRİNCİ DERECE BAĞLI TABLOLAR
-- =============================================

CREATE TABLE urun_markalari (
    id INT AUTO_INCREMENT PRIMARY KEY,
    urun_tipi_id INT NOT NULL,
    ad VARCHAR(50) NOT NULL,
    FOREIGN KEY (urun_tipi_id) REFERENCES urun_tipleri(id)
);

CREATE TABLE tedarikci_kisileri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tedarikci_id INT NOT NULL,
    ad_soyad VARCHAR(100) NOT NULL,
    gorevi VARCHAR(50) NULL,
    telefon VARCHAR(20) NULL UNIQUE,
    eposta VARCHAR(100) NULL,
    notlar TEXT NULL,
    FOREIGN KEY (tedarikci_id) REFERENCES tedarikciler(id)
);

CREATE TABLE tedarikci_odemeleri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tedarikci_id INT NOT NULL,
    tutar DECIMAL(18,2) NOT NULL CHECK (tutar > 0),
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tedarikci_id) REFERENCES tedarikciler(id)
);

CREATE TABLE alimlar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    toplam_tutar DECIMAL(18,2) NOT NULL DEFAULT 0,
    tedarikci_id INT NOT NULL,
    iptal_mi BOOLEAN DEFAULT 0,
    FOREIGN KEY (tedarikci_id) REFERENCES tedarikciler(id)
);

CREATE TABLE satislar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    toplam_tutar DECIMAL(18,2) NOT NULL DEFAULT 0,
    toplam_maliyet DECIMAL(18,2) NOT NULL DEFAULT 0,
    indirim DECIMAL(18,2) DEFAULT 0 CHECK (indirim >= 0),
    odeme_yontemi VARCHAR(50) NOT NULL CHECK (odeme_yontemi IN ('Nakit', 'Kredi Kartı', 'Havale')),
    musteri_id INT NOT NULL,
    iptal_mi BOOLEAN DEFAULT 0,
    FOREIGN KEY (musteri_id) REFERENCES musteriler(id)
);

-- =============================================
-- 3. İKİNCİ DERECE BAĞLI TABLOLAR
-- =============================================

CREATE TABLE urun_marka_modelleri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    marka_id INT NOT NULL,
    ad VARCHAR(50) NOT NULL,
    mevsim VARCHAR(20) NULL CHECK (mevsim IN ('Yaz', 'Kış', 'Dört Mevsim')),
    FOREIGN KEY (marka_id) REFERENCES urun_markalari(id)
);

-- =============================================
-- 4. ANA ÜRÜN TABLOSU
-- =============================================

CREATE TABLE urunler (
    id INT AUTO_INCREMENT PRIMARY KEY,
    barkod_qr VARCHAR(100) UNIQUE NULL,
    ad VARCHAR(100) NOT NULL,
    ebat VARCHAR(50) NULL,
    aciklama TEXT NULL,
    satis_fiyati DECIMAL(18,2) NOT NULL CHECK (satis_fiyati > 0),
    maliyet_fiyati DECIMAL(18,2) NULL,
    stok INT DEFAULT 0 CHECK (stok >= 0),
    fiziksel_urun_mu BOOLEAN DEFAULT 1,
    resim_yolu VARCHAR(255) NULL,
    silindi_mi BOOLEAN DEFAULT 0,
    urun_tipi_id INT NOT NULL,
    marka_id INT NOT NULL,
    marka_modeli_id INT NOT NULL,
    FOREIGN KEY (urun_tipi_id) REFERENCES urun_tipleri(id),
    FOREIGN KEY (marka_id) REFERENCES urun_markalari(id),
    FOREIGN KEY (marka_modeli_id) REFERENCES urun_marka_modelleri(id)
);

-- =============================================
-- 5. ÜRÜNE BAĞLI HAREKET TABLOLARI
-- =============================================

CREATE TABLE urun_partileri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    urun_id INT NOT NULL,
    miktar INT NOT NULL CHECK (miktar > 0),
    birim_maliyet DECIMAL(18,2) NOT NULL CHECK (birim_maliyet >= 0),
    eklenme_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (urun_id) REFERENCES urunler(id)
);

CREATE TABLE alim_kalemleri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alim_id INT NOT NULL,
    urun_id INT NOT NULL,
    urun_adi_anlik VARCHAR(100) NOT NULL,
    miktar INT NOT NULL CHECK (miktar > 0),
    birim_fiyat DECIMAL(18,2) NOT NULL CHECK (birim_fiyat >= 0),
    FOREIGN KEY (alim_id) REFERENCES alimlar(id),
    FOREIGN KEY (urun_id) REFERENCES urunler(id)
);

CREATE TABLE satis_kalemleri (
    id INT AUTO_INCREMENT PRIMARY KEY,
    satis_id INT NOT NULL,
    urun_id INT NOT NULL,
    urun_adi_anlik VARCHAR(100) NOT NULL,
    miktar INT NOT NULL CHECK (miktar > 0),
    birim_fiyat DECIMAL(18,2) NOT NULL CHECK (birim_fiyat >= 0),
    birim_maliyet DECIMAL(18,2) NOT NULL CHECK (birim_maliyet >= 0),
    iptal_mi BOOLEAN DEFAULT 0,
    FOREIGN KEY (satis_id) REFERENCES satislar(id),
    FOREIGN KEY (urun_id) REFERENCES urunler(id)
);

-- =============================================
-- 6. SİSTEM LOG/İPTAL TABLOSU
-- =============================================

CREATE TABLE iptal_kayitlari (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tarih DATETIME DEFAULT CURRENT_TIMESTAMP,
    kayit_turu VARCHAR(20) NOT NULL CHECK (kayit_turu IN ('Satis', 'Alim', 'Satis_Kalemi')),
    kayit_id INT NOT NULL,
    aciklama TEXT NULL,
    iptal_edilen_miktar INT NULL,
    iade_tutari DECIMAL(18,2) NULL,
    maliyet_tutari DECIMAL(18,2) NULL,
    iptal_eden VARCHAR(50) NULL
);

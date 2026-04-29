-- =============================================
-- 004 — PERFORMANS İNDEXLERİ
-- Zaten varsa hata vermemesi için her biri ayrı ayrı kontrol edilir.
-- MariaDB 10.1.4+ / MySQL 8.0.26+ için IF NOT EXISTS desteklenir.
-- =============================================

USE DijitalLastikServisiDB;

-- Tarih kolonları (ORDER BY tarih DESC, WHERE tarih BETWEEN)
CREATE INDEX IF NOT EXISTS idx_satislar_tarih         ON satislar(tarih);
CREATE INDEX IF NOT EXISTS idx_alimlar_tarih          ON alimlar(tarih);
CREATE INDEX IF NOT EXISTS idx_giderler_tarih         ON giderler(tarih);
CREATE INDEX IF NOT EXISTS idx_tedarikci_odemeleri_tarih ON tedarikci_odemeleri(tarih);
CREATE INDEX IF NOT EXISTS idx_iptal_kayitlari_tarih  ON iptal_kayitlari(tarih);
CREATE INDEX IF NOT EXISTS idx_urun_partileri_tarih   ON urun_partileri(eklenme_tarihi);

-- Sık filtre / arama
CREATE INDEX IF NOT EXISTS idx_urunler_silindi        ON urunler(silindi_mi, stok);
CREATE INDEX IF NOT EXISTS idx_urunler_ebat           ON urunler(ebat);
CREATE INDEX IF NOT EXISTS idx_satislar_musteri       ON satislar(musteri_id, tarih);
CREATE INDEX IF NOT EXISTS idx_satislar_odeme         ON satislar(odeme_yontemi);
CREATE INDEX IF NOT EXISTS idx_alimlar_tedarikci      ON alimlar(tedarikci_id, tarih);
CREATE INDEX IF NOT EXISTS idx_musteriler_plaka       ON musteriler(arac_plakasi);

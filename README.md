# Dijital Lastik Servisi Yönetim Sistemi

Lastik satış ve servis işletmesi için masaüstü + mobil yönetim sistemi.

## Modüller

- Ürün kataloğu & stok yönetimi (QR/barkod ile)
- Tedarikçi & borç takibi
- Alım yönetimi
- Müşteri & satış
- Tamir / servis hizmeti
- Gider takibi
- Günlük / haftalık / aylık raporlar

## Ekran Görüntüleri

### Masaüstü

**Dashboard** — günlük / aylık ciro, kâr, satış adedi ve genel durum özeti

![Masaüstü Dashboard](docs/screenshots/desktop-dashboard.png)

**Ürünler** — barkod/QR, ebat, marka, model, mevsim, satış-maliyet fiyatı ve stok takibi

![Masaüstü Ürünler](docs/screenshots/desktop-urunler.png)

**Tedarikçiler** — tedarikçi listesi ve güncel borç durumu, ödeme kaydı

![Masaüstü Tedarikçiler](docs/screenshots/desktop-tedarikciler.png)

**Müşteriler** — ad soyad, telefon, araç markası, plaka ve notlar

![Masaüstü Müşteriler](docs/screenshots/desktop-musteriler.png)

**Alımlar** — tedarikçi bazlı alım kayıtları ve tutarları

![Masaüstü Alımlar](docs/screenshots/desktop-alimlar.png)

**Lastik Oteli** — raf konumu, müşteri, lastik bilgisi, sezon ve teslim durumu

![Masaüstü Lastik Oteli](docs/screenshots/desktop-lastik-oteli.png)

**Raporlar** — tarih aralığına göre ciro/kâr/gider özeti, günlük kırılım ve en çok satanlar; PDF ve yazdırma çıktısı

![Masaüstü Raporlar](docs/screenshots/desktop-raporlar.png)

### Mobil

| Dashboard | Ürünler | Müşteriler | Lastik Oteli |
| --- | --- | --- | --- |
| ![Mobil Dashboard](docs/screenshots/mobile-dashboard.png) | ![Mobil Ürünler](docs/screenshots/mobile-urunler.png) | ![Mobil Müşteriler](docs/screenshots/mobile-musteriler.png) | ![Mobil Lastik Oteli](docs/screenshots/mobile-lastik-oteli.png) |

## Mimari

Bkz. [docs/architecture.md](docs/architecture.md)

## Kurulum

### VPS (ilk kurulum)
```bash
bash deploy/scripts/setup_vps.sh
```

### Güncelleme
```bash
bash deploy/scripts/deploy.sh
```

### Yerel Geliştirme (Backend)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # .env'i düzenle
uvicorn app.main:app --reload
```

API dökümantasyonu: `http://localhost:8000/docs`

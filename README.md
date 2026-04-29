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

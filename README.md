# Management Panel — VPS Dağıtım Kılavuzu

## Proje Yapısı

```
├── backend/                  ← VPS'e yüklenecek
│   ├── app/
│   │   ├── main.py           FastAPI uygulaması
│   │   ├── config.py         Ayarlar (.env ile)
│   │   ├── database.py       PostgreSQL bağlantısı
│   │   ├── models.py         SQLAlchemy modeller
│   │   ├── schemas.py        Pydantic şemalar
│   │   └── routers/          API endpoint'leri
│   │       ├── dashboard.py
│   │       ├── suppliers.py
│   │       ├── products.py
│   │       ├── customers.py
│   │       ├── sales.py
│   │       ├── purchases.py
│   │       ├── expenses.py
│   │       └── reports.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                 ← Windows bilgisayarda çalışacak
│   ├── main.py               PyQt6 ana pencere
│   ├── config.py             API_BASE_URL buradan ayarlanır
│   ├── api_client.py         HTTP API istemcisi
│   ├── requirements.txt
│   └── modules/              (Orijinal modüller, API'yi kullanacak şekilde güncellendi)
│
└── scripts/
    ├── vps_setup.sh          Ubuntu VPS kurulum scripti
    └── migrate_sqlite_to_postgres.py  Eski verileri taşıma scripti
```

---

## ADIM 1 — VPS Kurulumu

```bash
# VPS'e SSH ile bağlanın
ssh root@VPS_IP_ADRESI

# Kurulum scriptini çalıştırın
curl -O https://... # veya dosyayı kopyalayın
sudo bash vps_setup.sh
```

Script otomatik olarak şunları yapar:
- PostgreSQL kurar ve yapılandırır
- Uygulama kullanıcısı ve veritabanı oluşturur
- Python sanal ortamı kurar
- Systemd servisi oluşturur
- Nginx reverse proxy yapılandırır

---

## ADIM 2 — Backend Dosyalarını Kopyalama

```bash
# Windows'tan (PowerShell veya WSL)
scp -r backend/* root@VPS_IP_ADRESI:/opt/management_panel/

# Linux/Mac'ten
scp -r backend/* root@VPS_IP:/opt/management_panel/
```

---

## ADIM 3 — Python Paketlerini Kurma (VPS'te)

```bash
cd /opt/management_panel
venv/bin/pip install -r requirements.txt
```

---

## ADIM 4 — Servisi Başlatma

```bash
systemctl start management-panel
systemctl enable management-panel
systemctl status management-panel

# API'nin çalıştığını test edin:
curl http://localhost:8000/health
```

---

## ADIM 5 — Frontend Yapılandırması (Windows'ta)

`frontend/config.py` dosyasını açın ve VPS IP adresinizi girin:

```python
API_BASE_URL = "http://VPS_IP_ADRESI:8000"
```

Frontend bağımlılıklarını kurun:

```bash
pip install -r frontend/requirements.txt
```

Uygulamayı başlatın:

```bash
python frontend/main.py
```

---

## ADIM 6 — Eski Verileri Taşıma (Opsiyonel)

Eğer mevcut `management.db` SQLite dosyanızdaki verileri taşımak istiyorsanız:

```bash
# Backend klasöründen çalıştırın
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite path/to/management.db \
  --postgres "postgresql://mgmt_user:SIFRE@VPS_IP:5432/management_db"
```

---

## API Dokümantasyonu

Backend çalışırken tarayıcıdan erişebilirsiniz:

- **Swagger UI**: `http://VPS_IP:8000/docs`
- **ReDoc**: `http://VPS_IP:8000/redoc`

---

## Servis Yönetimi

```bash
# Durum kontrol
systemctl status management-panel

# Yeniden başlat
systemctl restart management-panel

# Logları izle
journalctl -u management-panel -f

# PostgreSQL bağlantı testi
sudo -u postgres psql -d management_db -c "SELECT COUNT(*) FROM products;"
```

---

## Güvenlik Notları

1. `.env` dosyasını güçlü şifrelerle doldurun
2. Üretim ortamında `DEBUG=false` olmalıdır
3. Firewall'da sadece 22 (SSH), 80 (HTTP) portlarını açık bırakın
4. SSL/HTTPS için Let's Encrypt kullanın: `certbot --nginx`
5. API_BASE_URL'yi `http://` yerine `https://` ile kullanın (SSL sonrası)

---

## Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| "Sunucuya bağlanılamadı" | VPS IP'sini config.py'de kontrol edin |
| "Connection refused" | `systemctl status management-panel` ile servisi kontrol edin |
| "PostgreSQL error" | `/opt/management_panel/.env` dosyasındaki DATABASE_URL'yi kontrol edin |
| Port 8000 erişilemiyor | `ufw allow 8000/tcp` veya cloud provider firewall kurallarını kontrol edin |

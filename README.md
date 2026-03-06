# Management Panel — Deployment Rehberi

## Mimari

```
[Windows/Mac — PyQt6 Masaüstü]
        |  HTTP (requests)
        v
[Ubuntu VPS — FastAPI + PostgreSQL]
  http://VPS_IP:8000/api/...
  http://VPS_IP:8000/docs   ← Swagger UI
```

---

## 1. VPS'e Backend Kurulumu (Tek Komut)

```bash
# Dosyaları VPS'e aktar
scp -r backend/ root@VPS_IP:/tmp/backend/
scp setup_vps.sh root@VPS_IP:/tmp/

# VPS'te şifreyi değiştir ve çalıştır
ssh root@VPS_IP
nano /tmp/setup_vps.sh   # DB_PASS satırını güncelle
sudo bash /tmp/setup_vps.sh
```

Script şunları otomatik yapar:
- PostgreSQL kurar, veritabanı ve kullanıcı oluşturur
- Python venv + bağımlılıkları yükler
- Systemd servisi kurar ve başlatır (reboot'ta otomatik başlar)

---

## 2. Doğrulama

```bash
# API çalışıyor mu?
curl http://VPS_IP:8000/
# {"status": "ok"}

# Swagger dokümantasyonu (tarayıcıdan):
http://VPS_IP:8000/docs
```

---

## 3. Frontend Kurulumu (Windows/Mac)

```bash
cd frontend/
pip install -r requirements.txt

# config.py'yi düzenle:
# API_BASE_URL = "http://VPS_IP:8000"

python main.py
```

---

## 4. Mevcut Veri Taşıma (SQLite → PostgreSQL)

```bash
# scripts/migrate_sqlite_to_postgres.py kullanın
# Önce management.db dosyasını VPS'e kopyalayın:
scp management.db root@VPS_IP:/tmp/

ssh root@VPS_IP
cd /opt/management_panel
source venv/bin/activate
python /tmp/scripts/migrate_sqlite_to_postgres.py /tmp/management.db
```

---

## 5. Servis Yönetimi

```bash
systemctl status management-panel    # Durum
systemctl restart management-panel   # Yeniden başlat
journalctl -u management-panel -f    # Canlı loglar
```

---

## 6. Güvenlik

```bash
# Sadece belirli IP'ye izin ver
ufw allow from OFIS_IP to any port 8000
ufw deny 8000

# HTTPS için Nginx + Certbot (önerilen):
apt install nginx certbot python3-certbot-nginx
```

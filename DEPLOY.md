# Deploy Rehberi

## Senin yapman gerekenler (özet)

1. VPS'e SSH bağlan
2. Repo'yu klonla / çek
3. `.env` dosyasını oluştur
4. DB migration'larını uygula
5. Admin kullanıcı oluştur
6. Backend servisini başlat
7. Nginx'i ayarla

---

## 1. VPS'e Bağlan

```bash
ssh root@45.39.241.111
```

---

## 2. Repo'yu Klonla

```bash
mkdir -p /opt/management-tire
cd /opt/management-tire
git clone https://github.com/MertCan-Aydin/management-tire.git .
```

**Eğer repo zaten klonlandıysa (güncelleme):**
```bash
cd /opt/management-tire
git pull
```

---

## 3. Uygulama Kullanıcısı + Python Ortamı

```bash
# Sistem kullanıcısı (uygulama root olarak çalışmaz)
id mgmttire &>/dev/null || useradd -r -s /bin/bash -d /opt/management-tire mgmttire
chown -R mgmttire:mgmttire /opt/management-tire

# Python
cd /opt/management-tire/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 4. .env Dosyası

```bash
cp /opt/management-tire/backend/.env.example /opt/management-tire/backend/.env
chmod 600 /opt/management-tire/backend/.env
nano /opt/management-tire/backend/.env
```

**.env içeriği (tüm `__DOLDUR__` alanlarını değiştir):**
```env
APP_ENV=production
APP_HOST=127.0.0.1
APP_PORT=8000
APP_DEBUG=false

DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=DijitalLastikServisiDB
DB_USER=lastik_user
DB_PASSWORD=MgmtPass_c285e8fb4d88

# En az 32 karakter rastgele: python3 -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET=BURAYA_32_KARAKTER_RASTGELE_YAZ

LOG_LEVEL=info
```

JWT_SECRET için rastgele değer üretmek:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 5. DB Migration — ÖNEMLİ

DB'nde orijinal Script-12.sql'den gelen tablolar ve SP'ler zaten var.
Bizim yeni SP'lerimiz farklı (filtre parametreli, JOIN'li). Önce eskilerini temizle:

### 5a. Mevcut SP'leri / Fonksiyonları / Trigger'ları Temizle

```bash
cd /opt/management-tire
mysql -u root -p DijitalLastikServisiDB < db/reset_procedures.sql
```

> **Not:** `root` yerine admin yetkili başka bir MySQL kullanıcın varsa onu kullan.
> `lastik_user` yalnızca EXECUTE yetkisine sahip olduğundan DDL çalıştıramaz.

### 5b. Auth Tablolarını Ekle (tablolar zaten varsa atlanır)

```bash
mysql -u root -p DijitalLastikServisiDB < db/migrations/001_tablolar.sql
```

> Bu dosya `IF NOT EXISTS` kullanır, mevcut tablolara dokunmaz.

### 5c. Yeni SP'leri Yükle

```bash
mysql -u root -p DijitalLastikServisiDB < db/migrations/002_stored_procedures.sql
mysql -u root -p DijitalLastikServisiDB < db/migrations/003_functions_triggers.sql
mysql -u root -p DijitalLastikServisiDB < db/migrations/005_auth.sql
mysql -u root -p DijitalLastikServisiDB < db/migrations/006_raporlar.sql
```

### 5d. Indexleri Ekle (sadece MariaDB 10.1.4+ / MySQL 8.0.26+)

```bash
mysql -u root -p DijitalLastikServisiDB < db/migrations/004_indexes.sql
```

> Hata alırsan atla — indexler performans için önemli ama zorunlu değil başlangıçta.

---

## 6. İlk Admin Kullanıcı

```bash
cd /opt/management-tire/backend
source .venv/bin/activate
python -m scripts.create_admin
```

Kullanıcı adı ve şifre gir. **Şifreyi not et.**

---

## 7. Backend Servisini Başlat (systemd)

```bash
cp /opt/management-tire/deploy/systemd/management-tire-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable management-tire-api
systemctl start management-tire-api

# Durum kontrolü
systemctl status management-tire-api

# Sağlık kontrolü
curl http://127.0.0.1:8000/health
# Beklenen: {"status":"ok","db":"ok","env":"production"}
```

---

## 8. Nginx Kurulumu (HTTPS)

```bash
# Nginx kur
apt install -y nginx certbot python3-certbot-nginx

# Config dosyasını kopyala
cp /opt/management-tire/deploy/nginx/management-tire.conf /etc/nginx/sites-available/management-tire.conf

# Config içindeki `server_name _` satırını IP veya domain ile değiştir
# Domain yoksa IP kullan: server_name 45.39.241.111;
nano /etc/nginx/sites-available/management-tire.conf

# Aktifleştir
ln -s /etc/nginx/sites-available/management-tire.conf /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

**Domain varsa SSL sertifikası al:**
```bash
certbot --nginx -d DOMAININ.com
```

**Domain yoksa (IP ile HTTP):**
nginx.conf içindeki SSL bölümünü kaldır, sadece 80 portu üzerinden çalıştır:
```nginx
server {
    listen 80;
    server_name 45.39.241.111;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 9. UFW (Güvenlik Duvarı)

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 3306/tcp   # MariaDB dışarıya kapalı
ufw --force enable
```

---

## 10. Güncelleme (Sonraki Deploylar)

```bash
cd /opt/management-tire
bash deploy/scripts/deploy.sh
```

---

## Hızlı Test (API Çalışıyor mu?)

```bash
# Swagger UI (sadece APP_DEBUG=true ise açık)
# http://45.39.241.111/docs

# Sağlık kontrolü
curl http://45.39.241.111/health

# Login testi
curl -X POST http://45.39.241.111/api/auth/giris \
  -d "username=KULLANICI_ADINIZ&password=PAROLANIZ"
```

---

## İstemci Tarafı Ayarları

### Masaüstü (PyQt6)
```
desktop/.env dosyasını oluştur:
API_BASE_URL=http://45.39.241.111   (HTTPS varsa https://)
```

### Mobil (Flutter)
```
mobile/lib/core/config.dart dosyasında:
const String kApiBaseUrl = 'http://45.39.241.111';
```

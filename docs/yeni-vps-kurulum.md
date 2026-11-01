# Yeni VPS Kurulum Rehberi

Dijital Lastik Servisi — sunucu taşıma veya sıfırdan kurulum.

> **Bu dökümanı bilgisayarında sakla.** VPS çöktüğünde GitHub'a erişimin varsa repo'dan da ulaşabilirsin, ama ekstra olarak PDF/ekran görüntüsü almanda fayda var.

---

## Adımlar

1. [Ön Hazırlık (kendi bilgisayarında)](#1-ön-hazırlık-kendi-bilgisayarında)
2. [Yeni VPS'e Bağlan](#2-yeni-vpse-bağlan)
3. [Otomatik Kurulum (tek komut)](#3-otomatik-kurulum-tek-komut)
4. [Veri Geri Yükleme (yedekten)](#4-veri-geri-yükleme-yedekten)
5. [.env Geri Yükleme](#5-env-geri-yükleme-opsiyonel)
6. [Yedekleme Sistemini Kur](#6-yedekleme-sistemini-tekrar-kur)
7. [Masaüstü & Mobil IP Güncelle](#7-masaüstü--mobil-ip-güncelle)
8. [Doğrulama Kontrolleri](#8-doğrulama-kontrolleri)
9. [Sabit Bilgiler & Referans](#9-sabit-bilgiler--referans)

---

## 1. Ön Hazırlık (kendi bilgisayarında)

VPS'e geçmeden önce her şeyin GitHub'da güncel olduğundan emin ol.

```bash
cd ~/Documents/management-tire
git add -A
git status              # değişiklikleri kontrol et
git commit -m "Son değişiklikler"
git push
```

> **Yedek anahtarın var mı?** `lastik-yedek-anahtar.txt` dosyası (age private key) kendi bilgisayarında veya şifre yöneticinde olmalı. Bu olmadan yedekler açılamaz.

Yedek repo'yu da güncelle:

```bash
cd ~/lastik-db-yedek && git pull
```

Bu klasör yoksa: `git clone git@github.com:MertCan-Aydin/lastik-db-yedek.git ~/lastik-db-yedek`

---

## 2. Yeni VPS'e Bağlan

Yeni VPS sağlayıcıdan aldıktan sonra SSH ile bağlan:

```bash
ssh root@YENI_VPS_IP
```

Ubuntu 22.04 veya 24.04 LTS önerilir. Minimum 1 GB RAM, 20 GB disk.

---

## 3. Otomatik Kurulum (tek komut)

`full_setup.sh` scripti her şeyi kurar: MariaDB, Python, Nginx, UFW, tüm migration'lar, systemd servisi.

```bash
# Repo'yu klonla
git clone https://github.com/MertCan-Aydin/management-tire.git /opt/management-tire
cd /opt/management-tire

# MariaDB root şifresini parametre olarak ver
bash deploy/scripts/full_setup.sh MARIADB_ROOT_SIFREN
```

> **MariaDB root şifresi:** MariaDB'yi bu script kuruyor. Yeni bir sunucuda genellikle root şifresi boş olur veya socket auth kullanılır.

### Script ne yapıyor?

| Adım | Açıklama |
|---|---|
| Paketler | python3, git, nginx, mariadb-server, certbot, ufw, fail2ban |
| UFW | 22 (SSH), 80, 443 açık — 3306 (MariaDB) kapalı |
| MariaDB | Veritabanı + `lastik_user` oluşturma |
| Migration'lar | 001 → 013 arası tüm SQL dosyaları sırayla |
| Python | venv + `requirements.txt` kurulumu |
| .env | Otomatik oluşturulur (DB şifresi + JWT secret rastgele) |
| systemd | `management-tire-api` servisi enable + start |
| Nginx | Reverse proxy (HTTP, port 80) |

Script sonunda şunu gösteriyorsa kurulum başarılı:

```
API Adresi:   http://YENI_IP
Health Check: http://YENI_IP/health

DB Bilgileri:
  Host:     127.0.0.1
  DB:       DijitalLastikServisiDB
  User:     lastik_user
  Password: (rastgele üretilmiş)
```

> **Bu bilgileri kaydet!** Ekranda gösterilen DB şifresi ve JWT secret'ı bir yere not al. `.env` dosyasında da var ama yedek olarak sakla.

---

## 4. Veri Geri Yükleme (yedekten)

Yedekleme sistemi kuruluysa veriler GitHub'da. VPS silinse bile müşteri, satış, stok verileri kurtarılır.

### A) Kendi bilgisayarında yedeği çöz

```bash
# En son yedeği bul
cd ~/lastik-db-yedek && git pull
ls -la dumps/       # yıl/ay klasörlerine bak

# Şifreyi çöz (age private key ile)
age -d -i ~/lastik-yedek-anahtar.txt \
    dumps/2026/11/DijitalLastikServisiDB-TARIH-SAAT.sql.gz.age \
    > /tmp/yedek.sql.gz

# Yeni VPS'e gönder
scp /tmp/yedek.sql.gz root@YENI_IP:/root/

# Temizle
rm /tmp/yedek.sql.gz
```

### B) VPS'te canlıya yükle

```bash
ssh root@YENI_IP

# Geri yükleme aracını kopyala (full_setup çalıştıysa zaten var)
cp /opt/management-tire/deploy/yedek/geri_yukle.sh /usr/local/sbin/lastik-geri-yukle
chmod +x /usr/local/sbin/lastik-geri-yukle

# Önce test kopyasına yükle (canlıya dokunmaz)
sudo lastik-geri-yukle /root/yedek.sql.gz

# Her şey doğru görünüyorsa canlıya yükle
sudo lastik-geri-yukle /root/yedek.sql.gz DijitalLastikServisiDB
```

> **Yedekleme sistemi kurulu değilse:** Eski veriler gitti demektir. Boş DB ile başlarsın. Uygulama ilk açılışta PIN kurulum ekranı gösterecek.

---

## 5. .env Geri Yükleme (opsiyonel)

Eski `.env` dosyasındaki JWT secret aynı kalırsa kullanıcıların mevcut oturumları bozulmaz. Yedekleme sistemi `.env`'yi de yedekliyordu:

```bash
# Kendi bilgisayarında:
age -d -i ~/lastik-yedek-anahtar.txt \
    ~/lastik-db-yedek/ek/opt_repo_backend_.env.age \
    > /tmp/env.txt

scp /tmp/env.txt root@YENI_IP:/opt/management-tire/backend/.env
rm /tmp/env.txt
```

Sonra VPS'te:

```bash
ssh root@YENI_IP
chmod 600 /opt/management-tire/backend/.env
chown mgmttire:mgmttire /opt/management-tire/backend/.env

# .env içindeki DB şifresini güncelle (yeni sunucuda farklı olabilir)
nano /opt/management-tire/backend/.env

# Servisi yeniden başlat
systemctl restart management-tire-api
```

.env yoksa veya geri yüklemeyeceksen: `full_setup.sh` zaten yeni bir tane oluşturdu. Sadece PIN ile yeniden giriş yaparsın.

---

## 6. Yedekleme Sistemini Tekrar Kur

Yeni VPS'te yedeklemeyi tekrar aktifleştirmelisin:

```bash
cd /opt/management-tire
sudo bash deploy/yedek/yedek_kurulum.sh
```

Script sana yeni bir **deploy key** gösterecek. GitHub'da:

1. Yedek repo → Settings → Deploy keys
2. **Eski VPS'in key'ini sil**
3. Yeni key'i ekle ("Allow write access" işaretli)

Script ayrıca şunları soracak:

- **age public key** — daha önce ürettiğin `age1...` değeri
- **Repo SSH adresi** — `git@github.com:MertCan-Aydin/lastik-db-yedek.git`
- **healthchecks.io URL** — varsa yapıştır, yoksa boş bırak

---

## 7. Masaüstü & Mobil IP Güncelle

Yeni VPS'in IP adresi değiştiyse istemcilerde güncelle:

### Masaüstü (PyQt6)

```
desktop/.env dosyasını düzenle:
API_BASE_URL=http://YENI_IP
```

### Mobil (Flutter)

```dart
// mobile/lib/core/config.dart dosyasında:
const String kApiBaseUrl = 'http://YENI_IP';
```

### SSL (HTTPS) istiyorsan

```bash
# Domain varsa:
certbot --nginx -d senindomain.com

# Sonra istemcilerde http:// yerine https:// kullan
```

---

## 8. Doğrulama Kontrolleri

- [ ] API sağlık kontrolü geçiyor mu?
  ```bash
  curl http://YENI_IP/health
  # Beklenen: {"status":"ok","db":"ok","env":"production"}
  ```

- [ ] Servis çalışıyor mu?
  ```bash
  systemctl status management-tire-api
  ```

- [ ] Nginx doğru çalışıyor mu?
  ```bash
  nginx -t
  curl -I http://YENI_IP
  ```

- [ ] Veritabanı tablo sayısı doğru mu?
  ```bash
  mysql -u root -p DijitalLastikServisiDB -e \
    "SELECT COUNT(*) AS tablolar FROM information_schema.TABLES WHERE TABLE_SCHEMA='DijitalLastikServisiDB';"
  ```

- [ ] Yedekleme timer'ı çalışıyor mu?
  ```bash
  systemctl list-timers lastik-yedek.timer
  ```

- [ ] Masaüstü uygulaması bağlanabiliyor mu?
- [ ] Mobil uygulama bağlanabiliyor mu?

---

## 9. Sabit Bilgiler & Referans

### Repo

| Bilgi | Değer |
|---|---|
| GitHub repo | `https://github.com/MertCan-Aydin/management-tire.git` |
| Kurulum scripti | `deploy/scripts/full_setup.sh` |
| Güncelleme scripti | `deploy/scripts/deploy.sh` |
| Yedek kurulum | `deploy/yedek/yedek_kurulum.sh` |

### VPS Dosya Yapısı

```
/opt/management-tire/           # Ana repo
  backend/                      # FastAPI backend
    .env                        # Gizli ayarlar (DB şifresi, JWT)
    .venv/                      # Python sanal ortam
  db/migrations/                # 001 → 013 SQL dosyaları
  deploy/
    scripts/full_setup.sh       # Sıfırdan kurulum
    scripts/deploy.sh           # Güncelleme
    systemd/                    # Servis dosyası
    nginx/                      # Nginx config
    yedek/                      # Yedekleme scriptleri

/etc/systemd/system/
  management-tire-api.service   # Backend servisi
  lastik-yedek.service          # Yedekleme servisi
  lastik-yedek.timer            # 3 saatte bir tetikleyici

/etc/lastik-yedek/              # Yedekleme ayarları
  my.cnf                        # yedek_user DB şifresi
  github_key                    # Deploy key
  alicilar.txt                  # age public key
  yedek.conf                    # Repo URL, healthchecks URL
```

### Veritabanı

| Bilgi | Değer |
|---|---|
| DB adı | `DijitalLastikServisiDB` |
| Uygulama kullanıcısı | `lastik_user` |
| Yedek kullanıcısı | `yedek_user` (sadece okuma) |
| Port | 3306 (sadece localhost, dışa kapalı) |

### Servis Komutları

```bash
# Backend
systemctl status management-tire-api
systemctl restart management-tire-api
journalctl -u management-tire-api -n 50 --no-pager

# Yedekleme
systemctl list-timers lastik-yedek.timer
sudo lastik-yedekle                    # elle yedek al
journalctl -u lastik-yedek -n 50

# Nginx
nginx -t && systemctl reload nginx

# Güncelleme (git pull + restart)
cd /opt/management-tire && bash deploy/scripts/deploy.sh
```

### Sorun Giderme

| Sorun | Çözüm |
|---|---|
| API yanıt vermiyor | `journalctl -u management-tire-api -n 50` ile logları kontrol et |
| DB bağlantı hatası | `.env` içindeki DB_PASSWORD'ü kontrol et, `systemctl status mariadb` |
| Nginx 502 Bad Gateway | Backend servisi çalışmıyor: `systemctl restart management-tire-api` |
| Migration hatası | Tek tek çalıştır: `mysql -u root -p DijitalLastikServisiDB < db/migrations/00X_dosya.sql` |
| Yedek push başarısız | Deploy key kontrol: `cat /etc/lastik-yedek/github_key.pub` → GitHub'da ekli mi? |

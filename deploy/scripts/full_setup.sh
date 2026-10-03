#!/bin/bash
# ============================================================
# Dijital Lastik Servisi — Sıfırdan Tam Kurulum
# Tek seferde çalıştır: bash full_setup.sh
# ============================================================
set -euo pipefail

# ── DEĞİŞKENLER (gerekirse düzenle) ────────────────────────
MYSQL_ROOT_PW="${1:?Kullanım: bash full_setup.sh MYSQL_ROOT_SIFRESI}"
DB_NAME="DijitalLastikServisiDB"
DB_USER="lastik_user"
DB_PASSWORD="$(openssl rand -hex 16)"
JWT_SECRET="$(openssl rand -hex 32)"
REPO_URL="https://github.com/MertCan-Aydin/management-tire.git"
REPO_DIR="/opt/management-tire"
APP_USER="mgmttire"
SERVER_IP="$(hostname -I | awk '{print $1}')"

LOG_FILE="/tmp/setup_log_$(date +%Y%m%d_%H%M%S).txt"

# ── YARDIMCI FONKSİYONLAR ──────────────────────────────────
step=0
ok()   { step=$((step+1)); echo ""; echo "=== [$step] OK: $1 ==="; }
fail() { echo ""; echo "!!! HATA [$step]: $1 !!!"; echo "Log: $LOG_FILE"; exit 1; }
run()  { "$@" >> "$LOG_FILE" 2>&1 || fail "$*"; }

echo "============================================"
echo " Dijital Lastik Servisi — Tam Kurulum"
echo " Log: $LOG_FILE"
echo " Sunucu IP: $SERVER_IP"
echo "============================================"

# ── 1. PAKETLER ─────────────────────────────────────────────
echo ""
echo "=== [1] Paketler kuruluyor... ==="
export DEBIAN_FRONTEND=noninteractive
run apt-get update
run apt-get install -y python3 python3-venv python3-pip git nginx mariadb-server certbot python3-certbot-nginx ufw fail2ban unattended-upgrades curl openssl
ok "Paketler kuruldu"

# ── 2. UFW ──────────────────────────────────────────────────
echo "=== [$((step+1))] UFW ayarlanıyor... ==="
run ufw allow OpenSSH
run ufw allow 80/tcp
run ufw allow 443/tcp
ufw deny 3306/tcp >> "$LOG_FILE" 2>&1 || true
echo "y" | ufw enable >> "$LOG_FILE" 2>&1 || true
ok "UFW aktif"

# ── 3. MARIADB BAŞLAT ──────────────────────────────────────
echo "=== [$((step+1))] MariaDB başlatılıyor... ==="
run systemctl enable mariadb
run systemctl start mariadb
ok "MariaDB çalışıyor"

# ── 4. VERİTABANI + KULLANICI ──────────────────────────────
echo "=== [$((step+1))] Veritabanı ve kullanıcı oluşturuluyor... ==="
mysql -u root -p"$MYSQL_ROOT_PW" >> "$LOG_FILE" 2>&1 <<SQL || fail "DB/kullanıcı oluşturma"
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
SQL
ok "DB: $DB_NAME  |  Kullanıcı: $DB_USER"

# ── 5. UYGULAMA KULLANICISI ───────────────────────────────
echo "=== [$((step+1))] Uygulama kullanıcısı oluşturuluyor... ==="
id -u "$APP_USER" &>/dev/null || useradd -r -s /bin/bash -d "$REPO_DIR" "$APP_USER"
ok "Kullanıcı: $APP_USER"

# ── 6. REPO KLONLA ────────────────────────────────────────
echo "=== [$((step+1))] Repo klonlanıyor... ==="
if [ -d "$REPO_DIR/.git" ]; then
    git config --global --add safe.directory "$REPO_DIR"
    cd "$REPO_DIR"
    run git pull --ff-only
    echo "  (repo zaten vardı, güncellendi)"
else
    run git clone "$REPO_URL" "$REPO_DIR"
fi
chown -R "$APP_USER:$APP_USER" "$REPO_DIR"
ok "Repo: $REPO_DIR"

# ── 7. MİGRATION DOSYALARINI DÜZELT (IF NOT EXISTS) ───────
echo "=== [$((step+1))] Migration dosyaları düzeltiliyor... ==="

# 001 — tablo oluşturmalara IF NOT EXISTS ekle
sed -i 's/CREATE TABLE \([a-z_]*\) (/CREATE TABLE IF NOT EXISTS \1 (/g' "$REPO_DIR/db/migrations/001_tablolar.sql"

# 002 — stored procedure'lere OR REPLACE ekle (MariaDB destekler)
sed -i 's/CREATE PROCEDURE/CREATE OR REPLACE PROCEDURE/g' "$REPO_DIR/db/migrations/002_stored_procedures.sql"

# 003 — function ve trigger'lara OR REPLACE ekle
sed -i 's/CREATE FUNCTION/CREATE OR REPLACE FUNCTION/g' "$REPO_DIR/db/migrations/003_functions_triggers.sql"
sed -i 's/CREATE TRIGGER/CREATE OR REPLACE TRIGGER/g' "$REPO_DIR/db/migrations/003_functions_triggers.sql"

# 005 — index'lere IF NOT EXISTS ekle, SP'lere OR REPLACE
sed -i 's/^CREATE INDEX /CREATE INDEX IF NOT EXISTS /g' "$REPO_DIR/db/migrations/005_auth.sql"
sed -i 's/CREATE PROCEDURE/CREATE OR REPLACE PROCEDURE/g' "$REPO_DIR/db/migrations/005_auth.sql"

# 006 — rapor SP'leri
sed -i 's/CREATE PROCEDURE/CREATE OR REPLACE PROCEDURE/g' "$REPO_DIR/db/migrations/006_raporlar.sql"

# 007 — pin login
sed -i 's/CREATE PROCEDURE/CREATE OR REPLACE PROCEDURE/g' "$REPO_DIR/db/migrations/007_pin_login.sql"
sed -i 's/CREATE TABLE \([a-z_]*\) (/CREATE TABLE IF NOT EXISTS \1 (/g' "$REPO_DIR/db/migrations/007_pin_login.sql"

# 008 — eprel
sed -i 's/CREATE PROCEDURE/CREATE OR REPLACE PROCEDURE/g' "$REPO_DIR/db/migrations/008_eprel.sql"
sed -i 's/CREATE TABLE \([a-z_]*\) (/CREATE TABLE IF NOT EXISTS \1 (/g' "$REPO_DIR/db/migrations/008_eprel.sql"

# 009 — lastik oteli
sed -i 's/CREATE PROCEDURE/CREATE OR REPLACE PROCEDURE/g' "$REPO_DIR/db/migrations/009_lastik_oteli.sql"
sed -i 's/CREATE TABLE \([a-z_]*\) (/CREATE TABLE IF NOT EXISTS \1 (/g' "$REPO_DIR/db/migrations/009_lastik_oteli.sql"

ok "Migration dosyaları idempotent hale getirildi"

# ── 8. MİGRATIONLARI ÇALIŞTIR ─────────────────────────────
echo "=== [$((step+1))] Migration'lar çalıştırılıyor... ==="
MIGRATION_OK=true
for f in "$REPO_DIR"/db/migrations/*.sql; do
    fname=$(basename "$f")
    echo -n "  $fname ... "
    if mysql -u root -p"$MYSQL_ROOT_PW" "$DB_NAME" < "$f" >> "$LOG_FILE" 2>&1; then
        echo "OK"
    else
        echo "HATA (detay: $LOG_FILE)"
        MIGRATION_OK=false
    fi
done
if $MIGRATION_OK; then
    ok "Tüm migration'lar başarılı"
else
    echo "  ⚠ Bazı migration'larda hata var — log'u kontrol et"
    ok "Migration'lar tamamlandı (uyarılı)"
fi

# ── 9. TABLO KONTROLÜ ─────────────────────────────────────
echo "=== [$((step+1))] Tablo kontrolü... ==="
TABLE_COUNT=$(mysql -u root -p"$MYSQL_ROOT_PW" "$DB_NAME" -N -e "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='$DB_NAME';" 2>/dev/null)
SP_COUNT=$(mysql -u root -p"$MYSQL_ROOT_PW" "$DB_NAME" -N -e "SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA='$DB_NAME' AND ROUTINE_TYPE='PROCEDURE';" 2>/dev/null)
echo "  Tablo sayısı: $TABLE_COUNT"
echo "  SP sayısı:    $SP_COUNT"
ok "DB doğrulama tamam"

# ── 10. PYTHON VENV ────────────────────────────────────────
echo "=== [$((step+1))] Python ortamı kuruluyor... ==="
cd "$REPO_DIR/backend"
python3 -m venv .venv
source .venv/bin/activate
run pip install -q -r requirements.txt
ok "Python bağımlılıkları kuruldu"

# ── 11. .ENV DOSYASI ───────────────────────────────────────
echo "=== [$((step+1))] .env dosyası oluşturuluyor... ==="
cat > "$REPO_DIR/backend/.env" <<ENVFILE
APP_ENV=production
APP_HOST=127.0.0.1
APP_PORT=8000
APP_DEBUG=false

DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_POOL_SIZE=5

JWT_SECRET=$JWT_SECRET
JWT_ALGORITHM=HS256
JWT_ACCESS_TTL_MIN=60
JWT_REFRESH_TTL_DAYS=30

LOG_LEVEL=info
ENVFILE
chmod 600 "$REPO_DIR/backend/.env"
chown "$APP_USER:$APP_USER" "$REPO_DIR/backend/.env"
ok ".env oluşturuldu"

# ── 12. SYSTEMD SERVİSİ ───────────────────────────────────
echo "=== [$((step+1))] systemd servisi kuruluyor... ==="
cp "$REPO_DIR/deploy/systemd/management-tire-api.service" /etc/systemd/system/
sed -i "s|/opt/repo|$REPO_DIR|g" /etc/systemd/system/management-tire-api.service
run systemctl daemon-reload
run systemctl enable management-tire-api
run systemctl restart management-tire-api
sleep 2
ok "systemd servisi aktif"

# ── 13. HEALTH CHECK ──────────────────────────────────────
echo "=== [$((step+1))] Sağlık kontrolü... ==="
HEALTH=$(curl -s http://127.0.0.1:8000/health 2>/dev/null || echo "BAĞLANTI YOK")
echo "  Yanıt: $HEALTH"
if echo "$HEALTH" | grep -q '"status":"ok"'; then
    ok "API çalışıyor"
else
    echo "  ⚠ API henüz yanıt vermiyor. Kontrol:"
    echo "    journalctl -u management-tire-api -n 30 --no-pager"
    ok "API kontrolü (uyarılı)"
fi

# ── 14. NGİNX ─────────────────────────────────────────────
echo "=== [$((step+1))] Nginx ayarlanıyor... ==="
cat > /etc/nginx/sites-available/management-tire.conf <<NGINX
server {
    listen 80;
    server_name $SERVER_IP;

    client_max_body_size 20M;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host \$host;
        proxy_set_header   X-Real-IP \$remote_addr;
        proxy_set_header   X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
    }
}
NGINX
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/management-tire.conf /etc/nginx/sites-enabled/
nginx -t >> "$LOG_FILE" 2>&1 || fail "Nginx config hatası"
run systemctl reload nginx
ok "Nginx aktif — http://$SERVER_IP"

# ── ÖZET ──────────────────────────────────────────────────
echo ""
echo "============================================"
echo " KURULUM TAMAMLANDI"
echo "============================================"
echo ""
echo " API Adresi:   http://$SERVER_IP"
echo " Health Check: http://$SERVER_IP/health"
echo ""
echo " DB Bilgileri:"
echo "   Host:     127.0.0.1"
echo "   DB:       $DB_NAME"
echo "   User:     $DB_USER"
echo "   Password: $DB_PASSWORD"
echo ""
echo " JWT Secret: $JWT_SECRET"
echo ""
echo " .env:       $REPO_DIR/backend/.env"
echo " Log:        $LOG_FILE"
echo ""
echo " Tablo: $TABLE_COUNT  |  SP: $SP_COUNT"
echo ""
echo " ─── SONRAKİ ADIMLAR ───"
echo " 1. Uygulama ilk açılışta PIN kurulum ekranı gelecek"
echo " 2. Domain varsa SSL ekle:"
echo "    certbot --nginx -d senindomain.com"
echo " 3. Masaüstü/mobil istemcide API adresini güncelle:"
echo "    API_BASE_URL=http://$SERVER_IP"
echo "============================================"

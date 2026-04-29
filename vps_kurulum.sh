#!/bin/bash
# ============================================================
# Dijital Lastik Servisi — Tek Komutla Tam VPS Kurulumu
# Kullanım: bash vps_kurulum.sh
# Root olarak VPS terminalinde çalıştır.
# ============================================================
set -e

# ── Renkler ─────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'
YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓ $1${NC}"; }
warn() { echo -e "${YELLOW}  ! $1${NC}"; }
step() { echo -e "\n${CYAN}══════════════════════════════════════${NC}"; \
         echo -e "${CYAN}  $1${NC}"; \
         echo -e "${CYAN}══════════════════════════════════════${NC}"; }
fail() { echo -e "${RED}  ✗ HATA: $1${NC}"; exit 1; }

# ── Sabitler (değiştirme) ────────────────────────────────────
REPO_URL="https://github.com/MertCan-Aydin/management-tire.git"
REPO_DIR="/opt/management-tire"
SERVICE="management-tire-api"
APP_USER="mgmttire"
DB_NAME="DijitalLastikServisiDB"
DB_USER="lastik_user"
DB_PASS="MgmtPass_c285e8fb4d88"
DB_HOST="127.0.0.1"

# ── Root kontrolü ────────────────────────────────────────────
[ "$EUID" -ne 0 ] && fail "Bu script root olarak çalıştırılmalı. Dene: sudo bash vps_kurulum.sh"

# ── Başlık ───────────────────────────────────────────────────
clear
echo -e "${CYAN}"
echo "  ██████╗ ██╗      ██████╗  ██████╗"
echo "  ██╔══██╗██║     ██╔═══██╗██╔════╝"
echo "  ██████╔╝██║     ██║   ██║██║  ███╗"
echo "  ██╔══██╗██║     ██║   ██║██║   ██║"
echo "  ██████╔╝███████╗╚██████╔╝╚██████╔╝"
echo "  ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝"
echo -e "${NC}"
echo -e "  ${YELLOW}Dijital Lastik Servisi — Otomatik Kurulum${NC}"
echo ""

# ── Admin kullanıcı bilgilerini al ───────────────────────────
echo -e "${YELLOW}Uygulama giriş bilgilerini belirle:${NC}"
echo -n "  Admin kullanıcı adı: "
read ADMIN_ADI
[ -z "$ADMIN_ADI" ] && fail "Kullanıcı adı boş olamaz"

while true; do
    echo -n "  Admin parolası (min 8 karakter): "
    read -s ADMIN_PAROLA; echo ""
    [ ${#ADMIN_PAROLA} -lt 8 ] && { warn "Parola en az 8 karakter olmalı"; continue; }
    echo -n "  Parola tekrar: "
    read -s ADMIN_PAROLA2; echo ""
    [ "$ADMIN_PAROLA" != "$ADMIN_PAROLA2" ] && { warn "Parolalar eşleşmiyor"; continue; }
    break
done
echo ""
echo -e "${GREEN}  Bilgiler alındı. Kurulum başlıyor...${NC}"
sleep 1

# ═══════════════════════════════════════════════════════════
step "1/9 — Sistem Paketleri"
# ═══════════════════════════════════════════════════════════
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
    python3 python3-venv python3-pip \
    git curl nginx ufw fail2ban \
    mariadb-client
ok "Paketler kuruldu"

# ═══════════════════════════════════════════════════════════
step "2/9 — Repo Klonlama / Güncelleme"
# ═══════════════════════════════════════════════════════════
if [ -d "$REPO_DIR/.git" ]; then
    cd "$REPO_DIR"
    git pull --ff-only
    ok "Repo güncellendi"
else
    git clone "$REPO_URL" "$REPO_DIR"
    ok "Repo klonlandı → $REPO_DIR"
fi

# ═══════════════════════════════════════════════════════════
step "3/9 — Uygulama Kullanıcısı & Python Ortamı"
# ═══════════════════════════════════════════════════════════
id -u "$APP_USER" &>/dev/null || useradd -r -s /bin/bash -d "$REPO_DIR" "$APP_USER"
ok "Kullanıcı: $APP_USER"

cd "$REPO_DIR/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
ok "Python ortamı hazır (.venv)"

# ═══════════════════════════════════════════════════════════
step "4/9 — .env Dosyası"
# ═══════════════════════════════════════════════════════════
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

cat > "$REPO_DIR/backend/.env" << ENV_EOF
# Otomatik oluşturuldu — $(date)
APP_ENV=production
APP_HOST=127.0.0.1
APP_PORT=8000
APP_DEBUG=false

DB_HOST=$DB_HOST
DB_PORT=3306
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASS
DB_POOL_SIZE=5

JWT_SECRET=$JWT_SECRET
JWT_ALGORITHM=HS256
JWT_ACCESS_TTL_MIN=60
JWT_REFRESH_TTL_DAYS=30

LOG_LEVEL=info
ENV_EOF

chmod 600 "$REPO_DIR/backend/.env"
chown "$APP_USER:$APP_USER" "$REPO_DIR/backend/.env"
ok ".env oluşturuldu (JWT secret otomatik üretildi)"

# ═══════════════════════════════════════════════════════════
step "5/9 — Veritabanı Kurulumu"
# ═══════════════════════════════════════════════════════════

# MariaDB unix socket ile root erişimi test et (şifresiz)
if mysql -e "SELECT 1;" &>/dev/null 2>&1; then
    MYSQL="mysql"
    ok "MariaDB'ye root erişimi tamam (socket auth)"
else
    warn "Socket auth çalışmadı. MariaDB root parolası gerekiyor."
    echo -n "  MariaDB root parolası: "
    read -s MYSQL_ROOT_PASS; echo ""
    MYSQL="mysql -p$MYSQL_ROOT_PASS"
    # Test
    $MYSQL -e "SELECT 1;" &>/dev/null 2>&1 || fail "MariaDB bağlantısı başarısız"
    ok "MariaDB bağlantısı tamam"
fi

# DB var mı?
$MYSQL -e "USE $DB_NAME;" &>/dev/null 2>&1 \
    || fail "Veritabanı '$DB_NAME' bulunamadı. Önce oluşturulmuş olması lazım."
ok "Veritabanı $DB_NAME bulundu"

# Mevcut SP / trigger / fonksiyonları temizle
echo "  Eski SP'ler, trigger'lar ve fonksiyonlar temizleniyor..."
$MYSQL "$DB_NAME" < "$REPO_DIR/db/reset_procedures.sql"
ok "Eski nesneler temizlendi"

# Migration'ları sırayla uygula
MIGRATIONS=(
    "001_tablolar.sql"
    "002_stored_procedures.sql"
    "003_functions_triggers.sql"
    "004_indexes.sql"
    "005_auth.sql"
    "006_raporlar.sql"
)

for mf in "${MIGRATIONS[@]}"; do
    echo "  Uygulanıyor: $mf"
    $MYSQL "$DB_NAME" < "$REPO_DIR/db/migrations/$mf" \
        || warn "$mf uygulanırken uyarı var (devam ediliyor)"
done
ok "Tüm migration'lar uygulandı"

# ═══════════════════════════════════════════════════════════
step "6/9 — İlk Admin Kullanıcı Oluşturma"
# ═══════════════════════════════════════════════════════════
cd "$REPO_DIR/backend"
source .venv/bin/activate

python3 - << PYTHON_EOF
import sys, os
sys.path.insert(0, '.')
os.chdir('$REPO_DIR/backend')

from dotenv import load_dotenv
load_dotenv('.env')

from app.core.security import hash_password
from app.core.db import get_cursor
from app.data_access import auth_dal

kullanici_adi = '$ADMIN_ADI'
parola_hash = hash_password('$ADMIN_PAROLA')

try:
    with get_cursor() as (cursor, _):
        mevcut = auth_dal.kullanici_adi_ile_getir(cursor, kullanici_adi)
        if mevcut:
            print(f'ZATEN_VAR')
        else:
            yeni_id = auth_dal.kullanici_olustur(cursor, kullanici_adi, parola_hash, 'admin')
            print(f'OK:{yeni_id}')
except Exception as e:
    print(f'HATA:{e}')
    sys.exit(1)
PYTHON_EOF

SONUC=$(python3 - << PYTHON_EOF 2>/dev/null
import sys, os
sys.path.insert(0, '.')
os.chdir('$REPO_DIR/backend')
from dotenv import load_dotenv
load_dotenv('.env')
from app.core.security import hash_password
from app.core.db import get_cursor
from app.data_access import auth_dal
kullanici_adi = '$ADMIN_ADI'
parola_hash = hash_password('$ADMIN_PAROLA')
try:
    with get_cursor() as (cursor, _):
        mevcut = auth_dal.kullanici_adi_ile_getir(cursor, kullanici_adi)
        if mevcut:
            print('ZATEN_VAR')
        else:
            yeni_id = auth_dal.kullanici_olustur(cursor, kullanici_adi, parola_hash, 'admin')
            print(f'OK:{yeni_id}')
except Exception as e:
    print(f'HATA:{e}')
    sys.exit(1)
PYTHON_EOF
)

case "$SONUC" in
    ZATEN_VAR) ok "Kullanıcı '$ADMIN_ADI' zaten var (şifre güncellenmedi)" ;;
    OK:*)       ok "Admin kullanıcı oluşturuldu → '$ADMIN_ADI'" ;;
    *)          fail "Admin oluşturulamadı: $SONUC" ;;
esac

# ═══════════════════════════════════════════════════════════
step "7/9 — Systemd Servisi"
# ═══════════════════════════════════════════════════════════
chown -R "$APP_USER:$APP_USER" "$REPO_DIR"

cp "$REPO_DIR/deploy/systemd/$SERVICE.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$SERVICE"
systemctl restart "$SERVICE"

sleep 3

# Sağlık kontrolü
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    ok "API çalışıyor → http://127.0.0.1:8000"
    DB_STATUS=$(curl -s http://127.0.0.1:8000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('db','?'))" 2>/dev/null || echo "?")
    ok "DB durumu: $DB_STATUS"
else
    warn "API henüz yanıt vermiyor (HTTP $HTTP_STATUS)"
    echo "  Log kontrol: journalctl -u $SERVICE -n 30"
fi

# ═══════════════════════════════════════════════════════════
step "8/9 — Nginx (HTTP)"
# ═══════════════════════════════════════════════════════════
PUBLIC_IP=$(curl -s -4 ifconfig.me 2>/dev/null || echo "IP_ALINAMADI")

cat > /etc/nginx/sites-available/management-tire.conf << NGINX_EOF
server {
    listen 80;
    server_name $PUBLIC_IP _;

    client_max_body_size 20M;

    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header Referrer-Policy no-referrer always;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host \$host;
        proxy_set_header   X-Real-IP \$remote_addr;
        proxy_set_header   X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/management-tire.conf /etc/nginx/sites-enabled/management-tire.conf
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
ok "Nginx hazır → http://$PUBLIC_IP"

# ═══════════════════════════════════════════════════════════
step "9/9 — Güvenlik Duvarı (UFW)"
# ═══════════════════════════════════════════════════════════
ufw allow OpenSSH   &>/dev/null
ufw allow 80/tcp    &>/dev/null
ufw allow 443/tcp   &>/dev/null
ufw deny  3306/tcp  &>/dev/null
ufw --force enable  &>/dev/null
ok "UFW aktif (22/80/443 açık, 3306 kapalı)"

# ═══════════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        KURULUM TAMAMLANDI  ✓             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}API Adresi  :${NC} http://$PUBLIC_IP"
echo -e "  ${CYAN}Sağlık test :${NC} curl http://$PUBLIC_IP/health"
echo -e "  ${CYAN}Admin giriş :${NC} $ADMIN_ADI"
echo ""
echo -e "  ${YELLOW}Masaüstü uygulaması .env:${NC}"
echo -e "    API_BASE_URL=http://$PUBLIC_IP"
echo ""
echo -e "  ${YELLOW}Mobil config.dart:${NC}"
echo -e "    const String kApiBaseUrl = 'http://$PUBLIC_IP';"
echo ""
echo -e "  ${YELLOW}Güncelleme için:${NC}"
echo -e "    cd $REPO_DIR && bash deploy/scripts/deploy.sh"
echo ""

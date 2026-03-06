#!/bin/bash
# ============================================================
# VPS Kurulum Scripti — Ubuntu 20/22/24 LTS
# Management Panel Backend + PostgreSQL
# Kullanım: sudo bash vps_setup.sh
# ============================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

print_step() { echo -e "\n${BLUE}==>${NC} $1"; }
print_ok()   { echo -e "${GREEN}✔${NC} $1"; }
print_warn() { echo -e "${YELLOW}⚠${NC} $1"; }

# ── Değiştirilebilir değişkenler ──────────────────────────────────────────────
DB_NAME="management_db"
DB_USER="mgmt_user"
DB_PASS="MgmtPass_$(openssl rand -hex 6)"   # Rastgele şifre üretilir
APP_DIR="/opt/management_panel"
API_PORT=8000

print_step "1/7 — Sistem güncelleniyor..."
apt-get update -qq && apt-get upgrade -y -qq
print_ok "Sistem güncellendi"

print_step "2/7 — Python 3.11 ve araçlar kuruluyor..."
apt-get install -y -qq python3.11 python3.11-venv python3-pip postgresql postgresql-contrib nginx curl
print_ok "Python ve PostgreSQL kuruldu"

print_step "3/7 — PostgreSQL veritabanı ve kullanıcı oluşturuluyor..."
systemctl start postgresql
systemctl enable postgresql

sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null || true
sudo -u postgres psql -c "DROP USER IF EXISTS ${DB_USER};" 2>/dev/null || true
sudo -u postgres psql << EOF
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
EOF
print_ok "Veritabanı oluşturuldu: ${DB_NAME}"

print_step "4/7 — Uygulama dizini hazırlanıyor..."
mkdir -p ${APP_DIR}
# NOT: backend dosyalarını buraya kopyalamanız gerekiyor:
# scp -r ./backend/* root@VPS_IP:${APP_DIR}/
print_warn "Backend dosyalarını ${APP_DIR} dizinine kopyalamanız gerekiyor"
print_warn "Komut: scp -r ./backend/* root@\$(hostname -I | awk '{print \$1}'):${APP_DIR}/"

print_step "5/7 — Python virtual environment ve paketler..."
python3.11 -m venv ${APP_DIR}/venv
${APP_DIR}/venv/bin/pip install --upgrade pip -q

# Eğer requirements.txt varsa kur
if [ -f "${APP_DIR}/requirements.txt" ]; then
    ${APP_DIR}/venv/bin/pip install -r ${APP_DIR}/requirements.txt -q
    print_ok "Python paketleri kuruldu"
else
    print_warn "requirements.txt bulunamadı — backend dosyalarını kopyaladıktan sonra çalıştırın:"
    print_warn "${APP_DIR}/venv/bin/pip install -r ${APP_DIR}/requirements.txt"
fi

print_step "6/7 — .env dosyası oluşturuluyor..."
cat > ${APP_DIR}/.env << ENVEOF
DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}
APP_NAME=Scalable Management Panel
APP_VERSION=1.0.0
DEBUG=false
SECRET_KEY=$(openssl rand -hex 32)
ENVEOF
chmod 600 ${APP_DIR}/.env
print_ok ".env dosyası oluşturuldu"

print_step "7/7 — Systemd servisi oluşturuluyor..."
cat > /etc/systemd/system/management-panel.service << SVCEOF
[Unit]
Description=Management Panel API
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT} --workers 2
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload

# Nginx reverse proxy (opsiyonel ama önerilen)
cat > /etc/nginx/sites-available/management-panel << NGINXEOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:${API_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/management-panel /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
systemctl enable nginx

# Firewall
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp   # SSH
    ufw allow 80/tcp   # HTTP
    ufw allow 8000/tcp # Doğrudan API erişimi (test için)
    print_ok "Firewall kuralları eklendi"
fi

# ── Özet ─────────────────────────────────────────────────────────────────────
VPS_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Kurulum tamamlandı!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  📁 Uygulama dizini : ${APP_DIR}"
echo -e "  🔑 DB Kullanıcı    : ${DB_USER}"
echo -e "  🔑 DB Şifresi      : ${YELLOW}${DB_PASS}${NC}  ← KAYDEDIN!"
echo -e "  🌐 API Adresi      : http://${VPS_IP}:${API_PORT}"
echo ""
echo -e "${YELLOW}Sonraki adımlar:${NC}"
echo -e "  1. Backend dosyalarını kopyalayın:"
echo -e "     scp -r ./backend/* root@${VPS_IP}:${APP_DIR}/"
echo -e "  2. Python paketlerini kurun:"
echo -e "     ${APP_DIR}/venv/bin/pip install -r ${APP_DIR}/requirements.txt"
echo -e "  3. Servisi başlatın:"
echo -e "     systemctl start management-panel"
echo -e "     systemctl enable management-panel"
echo -e "  4. Frontend config.py dosyasında API_BASE_URL değerini güncelleyin:"
echo -e "     API_BASE_URL = \"http://${VPS_IP}:${API_PORT}\""
echo ""

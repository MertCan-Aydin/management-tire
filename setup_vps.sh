#!/bin/bash
# ============================================================
# Management Panel - Ubuntu VPS Kurulum Scripti
# Kullanim: sudo bash setup_vps.sh
# ============================================================

set -e

DB_NAME="management_db"
DB_USER="mgmt_user"
DB_PASS="mgmt_pass_DEGISTIR"   # <-- BUNU DEGISTIRIN!
APP_DIR="/opt/management_panel"
SERVICE_USER="mgmtpanel"

echo "============================================"
echo " Management Panel VPS Kurulumu Basliyor..."
echo "============================================"

# 1. Sistem guncelleme
echo "[1/7] Sistem guncelleniyor..."
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx -qq

# 2. PostgreSQL kurulumu
echo "[2/7] PostgreSQL yapılandıriliyor..."
systemctl start postgresql
systemctl enable postgresql

sudo -u postgres psql << PSQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
    CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
  END IF;
END
\$\$;
CREATE DATABASE IF NOT EXISTS $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
PSQL

echo "PostgreSQL hazir: $DB_NAME / $DB_USER"

# 3. Uygulama kullanicisi
echo "[3/7] Uygulama kullanicisi olusturuluyor..."
id -u $SERVICE_USER &>/dev/null || useradd --system --no-create-home --shell /bin/false $SERVICE_USER

# 4. Uygulama dosyalari
echo "[4/7] Uygulama dosyalari kopyalaniyor..."
mkdir -p $APP_DIR
cp -r backend/* $APP_DIR/

# 5. Python virtual environment
echo "[5/7] Python ortami hazirlaniyor..."
python3 -m venv $APP_DIR/venv
$APP_DIR/venv/bin/pip install --upgrade pip -q
$APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt -q

chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR

# 6. Environment dosyasi
echo "[6/7] .env dosyasi olusturuluyor..."
cat > $APP_DIR/.env << ENV
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME
ENV

# 7. Systemd servisi
echo "[7/7] Systemd servisi olusturuluyor..."
cat > /etc/systemd/system/management-panel.service << SERVICE
[Unit]
Description=Management Panel FastAPI Backend
After=network.target postgresql.service

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable management-panel
systemctl start management-panel

echo ""
echo "============================================"
echo " KURULUM TAMAMLANDI!"
echo "============================================"
echo " API: http://$(hostname -I | awk '{print $1}'):8000"
echo " Docs: http://$(hostname -I | awk '{print $1}'):8000/docs"
echo ""
echo " Servis durumu: systemctl status management-panel"
echo " Loglar: journalctl -u management-panel -f"
echo ""
echo " ONEMLI: setup_vps.sh icindeki DB_PASS"
echo " degerini gercek bir sifre ile degistirin!"
echo "============================================"

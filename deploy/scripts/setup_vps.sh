#!/bin/bash
# İlk kurulum scripti — Ubuntu Server
set -e

REPO_URL="https://github.com/MertCan-Aydin/management-tire.git"
REPO_DIR="/opt/management-tire"
APP_USER="mgmttire"

echo "=== [1/8] Paketler güncelleniyor ==="
apt update && apt install -y python3 python3-venv python3-pip git nginx mariadb-server certbot python3-certbot-nginx ufw fail2ban unattended-upgrades

echo "=== [2/8] UFW kuralları ==="
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "=== [3/8] Uygulama kullanıcısı oluşturuluyor ==="
id -u "$APP_USER" &>/dev/null || useradd -r -s /bin/bash -d "$REPO_DIR" "$APP_USER"

echo "=== [4/8] Repo klonlanıyor ==="
git clone "$REPO_URL" "$REPO_DIR" 2>/dev/null || (cd "$REPO_DIR" && git pull)
chown -R "$APP_USER:$APP_USER" "$REPO_DIR"

echo "=== [5/8] Python venv + bağımlılıklar ==="
cd "$REPO_DIR/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt

echo "=== [6/8] .env dosyası ==="
if [ ! -f ".env" ]; then
    cp .env.example .env
    chmod 600 .env
    echo ""
    echo ">>> .env dosyası oluşturuldu. Şimdi düzenleyin:"
    echo "    nano $REPO_DIR/backend/.env"
    echo ">>> Ardından bu scripti tekrar çalıştırın veya migration'ı manuel uygulayın."
    exit 0
fi

echo "=== [7/8] DB migration'ları uygulanıyor ==="
source .env
for f in "$REPO_DIR"/db/migrations/*.sql; do
    echo "  Uygulanıyor: $f"
    mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" < "$f"
done

echo "=== [8/9] İlk admin kullanıcı oluşturuluyor ==="
cd "$REPO_DIR/backend"
source .venv/bin/activate
python -m scripts.create_admin

echo "=== [9/9] systemd servisi kuruluyor ==="
cp "$REPO_DIR/deploy/systemd/management-tire-api.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable management-tire-api
systemctl start management-tire-api

echo ""
echo "Kurulum tamamlandı!"
echo ""
echo "Nginx konfigürasyonu için:"
echo "  cp $REPO_DIR/deploy/nginx/management-tire.conf /etc/nginx/sites-available/management-tire.conf"
echo "  ln -s /etc/nginx/sites-available/management-tire.conf /etc/nginx/sites-enabled/"
echo "  nginx -t && systemctl reload nginx"
echo ""
echo "Servis durumu:"
systemctl status management-tire-api --no-pager -l | tail -5

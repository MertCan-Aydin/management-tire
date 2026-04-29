#!/bin/bash
set -e

REPO_DIR="/opt/repo"
SERVICE="management-tire-api"

echo "=== [1/5] Güncelleme alınıyor ==="
cd "$REPO_DIR"
git pull --ff-only

echo "=== [2/5] Python bağımlılıkları yükleniyor ==="
source backend/.venv/bin/activate
pip install -q -r backend/requirements.txt

echo "=== [3/5] Servis yeniden başlatılıyor ==="
sudo systemctl restart "$SERVICE"

echo "=== [4/5] Sağlık kontrolü ==="
sleep 2
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health)
if [ "$STATUS" != "200" ]; then
    echo "HATA: API yanıt vermiyor (HTTP $STATUS). Log: journalctl -u $SERVICE -n 50"
    exit 1
fi

echo "=== [5/5] Deploy tamamlandı ==="
systemctl status "$SERVICE" --no-pager -l | tail -5

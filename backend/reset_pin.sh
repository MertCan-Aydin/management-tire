#!/bin/bash
# PIN'i sıfırlar — bir sonraki uygulamada yeniden oluşturulur
ENV_FILE="/opt/management_panel/.env"

if grep -q "^PIN_HASH=" "$ENV_FILE"; then
    sed -i 's/^PIN_HASH=.*/PIN_HASH=/' "$ENV_FILE"
else
    echo "PIN_HASH=" >> "$ENV_FILE"
fi

systemctl restart management-panel
echo "✓ PIN sıfırlandı. Uygulama bir sonraki açılışta yeni PIN ister."

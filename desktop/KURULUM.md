# Masaüstü Uygulama Kurulumu

## Ön Koşullar

- Python 3.11+ kurulu olmalı
- Windows (PyQt6 için)

## Adımlar

```bash
# 1. Bu klasöre gel
cd desktop/

# 2. Sanal ortam oluştur
python -m venv .venv
.venv\Scripts\activate      # Windows

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. API adresini ayarla
copy .env.example .env
# .env içindeki API_BASE_URL'i güncelle:
# API_BASE_URL=https://SENIN_VPS_IP_VEYA_DOMAININ

# 5. Çalıştır
python main.py
```

## Önemli Notlar

- Token'lar Windows DPAPI aracılığıyla güvenli şekilde saklanır (`keyring` paketi)
- `.env` dosyası repoya commit edilmez
- API_BASE_URL HTTPS olmalı (self-signed sertifika için `verify=False` yapma)

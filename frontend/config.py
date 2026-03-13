import os


class Config:
    APP_NAME     = "Scalable Management Panel"
    APP_VERSION  = "1.0.0"

    # VPS API adresi — kendi VPS IP adresinizi girin
    API_BASE_URL = os.environ.get("API_BASE_URL", "http://VPS_IP_ADRESI:8000")

    # API Key — VPS'teki .env dosyasındaki API_KEY değeri ile aynı olmalı
    API_KEY      = os.environ.get("API_KEY", "API_KEY_BURAYA")

    BASE_DIR     = os.path.dirname(os.path.abspath(__file__))

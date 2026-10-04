import os
from dotenv import load_dotenv

load_dotenv()

# Not: VPS'te SSL sertifikası yoksa http:// kullanılır.
# Domain + Let's Encrypt sertifikası kurulduğunda https://'ye geçilebilir.
# strip + rstrip("/") → trailing whitespace ve slash temizlenir (kırık URL'leri önler)
API_BASE_URL = os.getenv("API_BASE_URL", "http://194.36.85.139").strip().rstrip("/")
APP_NAME = "Dijital Lastik Servisi"
TOKEN_SERVICE = "dijital-lastik"   # keyring servis adı

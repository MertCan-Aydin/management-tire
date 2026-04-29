import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "https://45.39.241.111")
APP_NAME = "Dijital Lastik Servisi"
TOKEN_SERVICE = "dijital-lastik"   # keyring servis adı

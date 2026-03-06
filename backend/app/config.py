from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Veritabanı
    DATABASE_URL: str = "postgresql://mgmt_user:mgmt_pass@localhost:5432/management_db"

    # Uygulama
    APP_NAME: str = "Scalable Management Panel"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Güvenlik (ileride JWT için)
    SECRET_KEY: str = "change-this-in-production-very-long-secret-key"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

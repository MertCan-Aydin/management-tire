from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://mgmt_user:mgmt_pass@localhost:5432/management_db"
    APP_NAME: str = "Scalable Management Panel"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-this-in-production"
    API_KEY: str = "change-me"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

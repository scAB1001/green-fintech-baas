# src/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Database
    DATABASE_URL: PostgresDsn = "postgresql+asyncpg://postgres:postgres@localhost:5432/green_fintech"

    # App
    PROJECT_NAME: str = "Green FinTech BaaS Simulator"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # API
    API_V1_STR: str = "/api/v1"


settings = Settings()

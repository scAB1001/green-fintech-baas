# src/app/core/config.py
"""Application configuration using Pydantic Settings."""

from __future__ import annotations

from pydantic import Field  # TODO: Use PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Green FinTech BaaS Simulator"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = str(Field("development", validation_alias="ENVIRONMENT"))

    # DB Settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "green_fintech"
    POSTGRES_PORT: int = 5432
    POSTGRES_INITDB_ARGS: str = "--auth=scram-sha-256"

    # Redis settings
    REDIS_PASSWORD: str = "7omaiwo32_K2~aagg+-xcjFmJ@a,32r3G"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def db_host(self) -> str:
        # If the code is running on your laptop, it MUST use localhost
        # to talk to the Docker ports you mapped.
        if self.is_production:
            return "green-fintech-db"  # pragma: no cover
        return "localhost"

    @property
    def DATABASE_URL(self) -> str:
        """Build database URL from components or use environment variable."""
        import os

        explicit_url = os.environ.get("DATABASE_URL")
        if explicit_url:
            return explicit_url

        # Fallback for local development outside of Docker
        host = (
            "green-fintech-db" if self.is_production else "localhost"
        )  # pragma: no cover
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{host}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def REDIS_URL(self) -> str:
        """Build Redis URL from components or use environment variable."""
        import os

        explicit_url = os.environ.get("REDIS_URL")
        if explicit_url:
            return explicit_url

        # Fallback for local development
        host = (
            "green-fintech-db" if self.is_production else "localhost"
        )  # pragma: no cover
        return f"redis://:{self.REDIS_PASSWORD}@{host}:6379"


settings = Settings()

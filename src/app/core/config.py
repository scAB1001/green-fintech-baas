"""Application configuration using Pydantic Settings."""

from __future__ import annotations

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    PROJECT_NAME: str = "Green FinTech BaaS Simulator"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = str(Field("development", validation_alias="ENVIRONMENT"))
    API_V1_STR: str = "/api/v1"

    # Database (placeholder - will be used in later branch)
    POSTGRES_DATABASE_URL: PostgresDsn | None = None

    # Security
    SECRET_KEY: str = "development-secret-key-change-in-production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    # Load .env variables for database configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "green_fintech"
    POSTGRES_PORT: int = 5432
    POSTGRES_INITDB_ARGS: str = "--auth=scram-sha-256"

    @property
    def DATABASE_URL(self) -> PostgresDsn:
        """Build database URL from components."""
        return PostgresDsn(f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@localhost:{self.POSTGRES_PORT}/{self.POSTGRES_DB}")

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Sync URL for Alembic."""
        return str(self.DATABASE_URL).replace('+asyncpg', '')

settings = Settings()

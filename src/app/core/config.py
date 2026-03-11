# src/app/core/config.py
"""
Application Configuration Management.

This module utilizes Pydantic Settings to validate and manage environment
variables. It provides a strongly-typed, centralized registry for all
database, caching, and environment configurations, ensuring that the application
fails fast on startup if critical infrastructure secrets are missing.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore[misc]
    """
    Global application settings instantiated from environment variables.

    Pydantic automatically reads from the local `.env` file or the system's
    environment variables. Sensitive credentials (passwords, tokens) are
    strictly omitted from this source file and must be injected via the environment.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Green FinTech BaaS Simulator"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field("development", validation_alias="ENVIRONMENT")

    # DB Settings (Required from .env)
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int
    POSTGRES_INITDB_ARGS: str

    # Redis settings (Required from .env)
    REDIS_PASSWORD: str

    @property
    def is_development(self) -> bool:
        """Determines if the application is running locally."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Determines if the application is running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def db_host(self) -> str:
        """Dynamically resolves the database host based on the execution environment."""
        if self.is_production:
            return "green-fintech-db"  # pragma: no cover
        return "localhost"

    @property
    def DATABASE_URL(self) -> str:
        """Constructs the SQLAlchemy asynchronous connection string."""
        import os

        explicit_url = os.environ.get("DATABASE_URL")
        if explicit_url:
            return explicit_url

        host = (
            "green-fintech-db" if self.is_production else "localhost"
        )  # pragma: no cover
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{host}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def REDIS_URL(self) -> str:
        """Constructs the Redis connection string."""
        import os

        explicit_url = os.environ.get("REDIS_URL")
        if explicit_url:
            return explicit_url

        host = (
            "green-fintech-db" if self.is_production else "localhost"
        )  # pragma: no cover
        return f"redis://:{self.REDIS_PASSWORD}@{host}:6379"


# Tell the static type checker to ignore missing arguments,
# as Pydantic injects them dynamically from the environment.
settings = Settings()

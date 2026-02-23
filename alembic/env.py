# alembic/env.py
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.database import Base

# THIS IS CRITICAL - Add your src directory to Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import your SQLAlchemy Base and models

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from your settings (sync version for migrations)
# Remove +asyncpg for sync operations
sync_url = str(settings.DATABASE_URL).replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", sync_url)

# Add your model's MetaData object for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using sync engine."""
    # Use sync engine_from_config, NOT async_engine_from_config
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

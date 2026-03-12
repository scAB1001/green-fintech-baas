# alembic/env.py
"""
Alembic Environment Configuration.

This module bootstraps the Alembic migration context. It connects the
SQLAlchemy ORM metadata from our application to Alembic's inspection engine,
allowing it to auto-generate and apply DDL (Data Definition Language) changes.
"""

import sys
from pathlib import Path

# We must insert the 'src' directory into the system path before Alembic
# attempts to import our application models. This bridges the gap between
# the Alembic CLI execution context and our project's Domain-Driven structure.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.database.session import Base
from app.core.config import settings

# Alembic needs to load the model definitions into memory so it can compare
# the ORM state against the actual database schema. (These are usually
from app.models.company import Company  # noqa: F401
from app.models.environmental_metric import EnvironmentalMetric  # noqa: F401
from app.models.loan_simulation import LoanSimulation  # noqa: F401
from app.models.national_energy import NationalEnergy  # noqa: F401
from app.models.regional_emission import RegionalEmission  # noqa: F401

# Access the Alembic Config object, which provides access to the values
# within the alembic.ini file in use.
config = context.config

# Interpret the config file for Python logging. This sets up loggers
# based on the definitions in alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic natively prefers synchronous database connections for schema inspection
# and migration generation in this specific setup. We strip the asynchronous
# driver (+asyncpg) from our application's database URL to force a standard
# synchronous connection (e.g., via psycopg2) during the migration phase.
sync_url = str(settings.DATABASE_URL).replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", sync_url)

# Bind the target metadata so Alembic's 'autogenerate' feature can inspect
# our SQLAlchemy Base classes and detect schema changes.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Executes database migrations in 'offline' mode.

    In this mode, Alembic configures the context with just a URL
    and does not create a live Engine. It generates raw SQL scripts directly
    to standard output or a specified file, rather than executing them against
    the database. This is useful for DBA reviews.

    Returns:
        None
    """
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
    """
    Executes database migrations in 'online' mode.

    In this mode, Alembic creates a synchronous database connection pool
    and associates it with the migration context. This allows Alembic to
    inspect the current database state and execute DDL commands directly
    against the live PostgreSQL instance.

    Returns:
        None
    """
    # We deliberately use the synchronous engine_from_config here,
    # mapping to the stripped URL we configured above.
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

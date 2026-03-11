# src/app/database/session.py
"""
Asynchronous Database Session Management.



This module establishes the core SQLAlchemy 2.0 asynchronous engine and
session factory. It leverages the 'asyncpg' driver for high-performance,
non-blocking database I/O, which is critical for the BaaS under heavy load.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Ensure the database URL explicitly requests the asynchronous asyncpg driver.
# This acts as a safety net if the environment variable was misconfigured
# with a standard synchronous PostgreSQL prefix.
database_url = str(settings.DATABASE_URL)
if database_url and "+asyncpg" not in database_url:
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

# Initialize the core SQLAlchemy asynchronous engine.
# - pool_pre_ping: Tests connections for liveness before checkout to prevent
#   unexpected drops or connection closed exceptions.
# - pool_size/max_overflow: Tuned for standard FastAPI worker concurrency.
engine = create_async_engine(
    database_url,
    echo=settings.is_development,  # Stream raw SQL logs only in development
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)

# Configure the session factory.
# expire_on_commit=False is strictly required for async SQLAlchemy. It prevents
# the ORM from implicitly triggering lazy-loads (which require synchronous I/O)
# after the session transaction has been successfully committed.
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# The centralized declarative base class that all ORM models will inherit from.
# Alembic relies on this Base metadata to autogenerate schema migrations.
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provisions a database session per HTTP request.

    Utilizes an asynchronous context manager to ensure that the database
    session is reliably rolled back or closed, and returned to the connection
    pool upon request completion or failure, preventing memory leaks.

    Yields:
        AsyncSession: An isolated, asynchronous SQLAlchemy database session.
    """
    async with AsyncSessionLocal() as session:
        yield session

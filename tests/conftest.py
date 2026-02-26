# tests/conftest.py
import asyncio
import json
import pathlib
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.database import Base
from app.database.session import get_db
from app.main import app
from app.models.company import Company


# --- pytest-docker fixtures ---
@pytest.fixture(scope="session")
def docker_compose_file():
    # Points exactly to your test-specific compose
    return str(Path(__file__).parent / "docker" / "compose.yaml")


@pytest.fixture(scope="session")
def test_db_url(docker_ip, docker_services) -> str:
    port = docker_services.port_for("postgres_test", 5432)
    db_url = f"postgresql+asyncpg://postgres:postgres@{docker_ip}:{port}/green_fintech_test"

    # Synchronous health check to satisfy wait_until_responsive
    def is_db_responsive():
        try:
            import psycopg
            conn = psycopg.connect(
                host=docker_ip,
                port=port,
                user="postgres",
                password="postgres",
                dbname="postgres",
                connect_timeout=1
            )
            conn.close()
            return True
        except Exception:
            return False

    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.5, check=is_db_responsive)
    return db_url


# --- The "Scope-Fixing" Engine ---
@pytest_asyncio.fixture(scope="function")
async def test_engine(test_db_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """Fresh engine for every test to avoid 'Closed Loop' errors."""
    engine = create_async_engine(
        test_db_url,
        poolclass=NullPool,  # Don't pool connections across different loops
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Function-scoped session using a clean connection.
    We use a transaction to ensure rollback after the test.
    """
    async with test_engine.connect() as connection:
        # Start a transaction
        transaction = await connection.begin()

        # Bind the session to this specific connection
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint"
        )

        yield session

        # Cleanup
        await session.close()
        await transaction.rollback()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Industry-standard AsyncClient setup.
    Uses ASGITransport to bridge httpx directly to the FastAPI app.
    Override the app's get_db dependency to use the test session.
    """
    # 1. Setup Dependency Injection
    def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db

    # 2. Define the ASGI Transport
    transport = ASGITransport(app=app)

    # 3. Initialize Client
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver"
    ) as ac:
        yield ac

    # 4. Cleanup
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_companies(db_session: AsyncSession):
    """Populate the test database with standard company data."""
    fixture_path = pathlib.Path(__file__).parent / "fixtures" / "companies.json"
    with open(fixture_path) as f:
        data = json.load(f)

    companies = [Company(**item) for item in data]
    db_session.add_all(companies)
    await db_session.flush()
    return companies


@pytest_asyncio.fixture
async def seed_metrics(db_session: AsyncSession, seed_companies):
    """Populate the test database with standard environmental metrics."""
    fixture_path = pathlib.Path(__file__).parent / "fixtures" / "metrics.json"
    with open(fixture_path) as f:
        data = json.load(f)

    # Map company names to IDs for foreign key relationships
    company_map = {c.name: c.id for c in seed_companies}

    for item in data:
        item["company_id"] = company_map.get(item["company_name"])
        del item["company_name"]  # Remove name, we only need ID

    from app.models.environmental_metric import EnvironmentalMetric
    metrics = [EnvironmentalMetric(**item) for item in data]
    db_session.add_all(metrics)
    await db_session.flush()
    return metrics

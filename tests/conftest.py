# tests/conftest.py
import asyncio
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


# @pytest_asyncio.fixture(scope="session")
# async def test_engine(test_db_url: str) -> AsyncGenerator[AsyncEngine, None]:
#     """
#     Session-scoped engine.
#     In pytest-asyncio 0.23+, 'asyncio_default_test_loop_scope' handles the runner.
#     """
#     engine = create_async_engine(test_db_url, echo=False)

#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

#     yield engine
#     await engine.dispose()

@pytest_asyncio.fixture(scope="function")  # Match the test scope
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

# @pytest_asyncio.fixture
# async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
#     """Function-scoped session with automatic rollback."""
#     async_session = async_sessionmaker(
#         test_engine, class_=AsyncSession, expire_on_commit=False)

#     async with async_session() as session, session.begin():
#             yield session
#             # Rolling back ensures Test A doesn't affect Test B
#             await session.rollback()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Industry-standard AsyncClient setup.
    Uses ASGITransport to bridge httpx directly to the FastAPI app.
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

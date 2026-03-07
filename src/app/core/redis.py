# src/app/core/redis.py
from collections.abc import AsyncGenerator

import redis.asyncio as redis

from app.core.config import settings

# The global connection pool manager
redis_client = redis.from_url(
    settings.REDIS_URL, encoding="utf-8", decode_responses=True
)


async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    """
    FastAPI dependency that injects the Redis client.
    Yielding it allows us to easily mock it during pytest runs.
    """
    yield redis_client  # pragma: no cover


async def clear_cache(company_id: int) -> None:
    """Call for 'update' or 'delete' services to prevent stale data."""
    await redis_client.delete(f"company:{company_id}")

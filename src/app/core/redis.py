# src/app/core/redis.py
"""
Redis Connection Management.



This module initializes and manages the global asynchronous Redis connection pool.
It provides FastAPI dependencies for injecting the Redis client into route handlers,
ensuring efficient connection reuse and simplifying unit test mocking.
"""

from collections.abc import AsyncGenerator

import redis.asyncio as redis

from app.core.config import settings

# Initialize the global connection pool manager.
# We use decode_responses=True so Redis automatically decodes byte payloads
# into UTF-8 strings, saving us from manual decoding in the service layer.
redis_client = redis.from_url(
    settings.REDIS_URL, encoding="utf-8", decode_responses=True
)


async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    """
    FastAPI dependency that yields the asynchronous Redis client.

    By yielding the client rather than returning it directly, we seamlessly
    integrate with FastAPI's dependency injection system. This is critical
    for overriding the cache with a mock object during pytest runs.

    Yields:
        redis.Redis: The active Redis connection from the global pool.
    """
    yield redis_client  # pragma: no cover


async def clear_cache(company_id: int) -> None:
    """
    Invalidates the specific cache entry for a given corporate entity.

    This function must be called immediately after any state-mutating
    service operations (e.g., UPDATE or DELETE) to prevent the API from
    serving stale data on subsequent GET requests.

    Args:
        company_id (int): The unique identifier of the company to evict.
    """
    await redis_client.delete(f"company:{company_id}")

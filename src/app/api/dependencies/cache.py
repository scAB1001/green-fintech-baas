# src/app/api/dependencies/cache.py
import json
from typing import Any

from redis.asyncio import Redis


async def get_cached_object(cache: Redis, cache_key: str) -> dict[str, str] | None:
    """Retrieves and deserializes an object from Redis."""
    data = await cache.get(cache_key)
    return json.loads(data) if data else None


async def set_cached_object(
    cache: Redis,
    cache_key: str,
    data: dict[str, Any] | list[dict[str, Any]],
    expire: int = 3600
) -> None:
    """Serializes and stores an object in Redis with a TTL."""
    await cache.setex(cache_key, expire, json.dumps(data))


async def invalidate_cache(cache: Redis, cache_key: str) -> None:
    """Deletes a specific key from Redis."""
    await cache.delete(cache_key)


async def invalidate_pattern(cache: Redis, pattern: str) -> None:
    """
    Finds and deletes all keys matching a specific pattern (e.g. pagination).
    """
    keys = await cache.keys(pattern)
    if keys:
        await cache.delete(*keys)

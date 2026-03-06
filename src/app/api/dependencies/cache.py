# src/app/api/dependencies/cache.py
import json

from redis.asyncio import Redis


async def get_cached_object(cache: Redis, cache_key: str) -> dict | None:
    """Retrieves and deserializes an object from Redis."""
    data = await cache.get(cache_key)
    return json.loads(data) if data else None


async def set_cached_object(cache: Redis, cache_key: str,
                            data: dict, expire: int = 3600):
    """Serializes and stores an object in Redis with a TTL."""
    await cache.setex(cache_key, expire, json.dumps(data))


async def invalidate_cache(cache: Redis, cache_key: str):
    """Deletes a specific key from Redis."""
    await cache.delete(cache_key)

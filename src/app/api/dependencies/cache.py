# src/app/api/dependencies/cache.py
"""
Redis Caching Dependencies.

This module provides asynchronous utility functions for interacting with the
Redis caching layer. It abstracts the serialization and deserialization
logic (JSON) and provides mechanisms for targeted or pattern-based cache
invalidation to maintain data consistency across the API.


"""

import json
from typing import Any

from redis.asyncio import Redis


async def get_cached_object(cache: Redis, cache_key: str) -> dict[str, Any] | None:
    """
    Retrieves and deserializes a JSON object from the Redis cache.

    Args:
        cache (Redis): The active asynchronous Redis connection.
        cache_key (str): The unique identifier for the cached resource.

    Returns:
        dict[str, Any] | None: The parsed Python dictionary if the key exists,
        otherwise None if it's a cache miss.
    """
    data = await cache.get(cache_key)
    # Deserialize the payload back into a Python dictionary upon a cache hit
    return json.loads(data) if data else None


async def set_cached_object(
    cache: Redis,
    cache_key: str,
    data: dict[str, Any] | list[dict[str, Any]],
    expire: int = 3600,
) -> None:
    """
    Serializes and stores a Python object in Redis with a Time-To-Live (TTL).

    Args:
        cache (Redis): The active asynchronous Redis connection.
        cache_key (str): The unique identifier for the cached resource.
        data (dict[str, Any] | list[dict[str, Any]]): The payload to serialize.
        expire (int, optional): The TTL in seconds. Defaults to 3600 (1 hour).

    Returns:
        None
    """
    # We use setex (Set with Expiration) to ensure stale data is automatically
    # purged from the cache without requiring a manual cron job or cleanup routine.
    await cache.setex(cache_key, expire, json.dumps(data))


async def invalidate_cache(cache: Redis, cache_key: str) -> None:
    """
    Deletes a specific, exact-match key from the Redis cache.

    Typically called after a state-mutating operation (POST, PATCH, DELETE)
    to ensure subsequent GET requests fetch fresh data from PostgreSQL.

    Args:
        cache (Redis): The active asynchronous Redis connection.
        cache_key (str): The exact unique identifier to delete.

    Returns:
        None
    """
    await cache.delete(cache_key)


async def invalidate_pattern(cache: Redis, pattern: str) -> None:
    """
    Finds and deletes all keys matching a specific string pattern.

    Crucial for invalidating paginated lists or grouped resources where
    a single database mutation invalidates multiple cached views (e.g.,
    clearing all `companies:list:page:*` keys when a new company is added).

    Args:
        cache (Redis): The active asynchronous Redis connection.
        pattern (str): The wildcard pattern to match (e.g., 'companies:*').

    Returns:
        None
    """
    # Warning: The KEYS command operates in O(N) time and can block the Redis
    # event loop if the dataset is massive. For a BaaS of this scale, it is
    # acceptable, but consider SCAN for enterprise-scale deployments.
    keys = await cache.keys(pattern)
    if keys:
        await cache.delete(*keys)

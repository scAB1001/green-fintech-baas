# src/app/core/redis.py
import redis.asyncio as redis

from app.core.config import settings

# This will now automatically be localhost or the container name
redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)

# TODO: Remove or convert to use async instance --ss this needed.
# async def get_redis_client():
#     """Returns the redis client instance."""
#     return redis_client

async def clear_cache(company_id: int):
    """Call for 'update' or 'delete' services to prevent stale data."""
    await redis_client.delete(f"company:{company_id}")

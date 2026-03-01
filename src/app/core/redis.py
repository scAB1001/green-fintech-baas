import os

import redis.asyncio as redis

# Get the URL from environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = redis.from_url(
    REDIS_URL, encoding="utf-8", decode_responses=True)

async def get_redis_client():
    return redis_client

# Inside update_company service, update the stale
# await r.delete(f"company:{company_id}")

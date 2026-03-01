# src/app/core/redis.py
import os

import redis.asyncio as redis

# If running uvicorn locally, use localhost.
# If running inside Docker, use the container name.
# REDIS_LOCAL_HOST = os.getenv("REDIS_HOST", "localhost")
# REDIS_REMOTE_HOST = os.getenv("REDIS_HOST", "green-fintech-cache")
# REDIS_PORT = os.getenv("REDIS_PORT", "6379")

# redis_client = redis.from_url(
#     f"redis://{REDIS_LOCAL_HOST}:{REDIS_PORT}",
#     encoding="utf-8",
#     decode_responses=True
# )

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# 2. Initialize the client using the resolved URL
redis_client = redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)

# Inside update_company service, update the stale cached data in redis after each
# await r.delete(f"company:{company_id}")

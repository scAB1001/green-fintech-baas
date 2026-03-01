# src/app/api/dependencies/cache.py
# import json
# from typing import Type, TypeVar, Optional
# from fastapi import Depends
# from pydantic import BaseModel
# from app.core.redis import get_redis_client
# import redis.asyncio as redis_lib

# T = TypeVar("T", bound=BaseModel)


# class CacheManager:
#     def __init__(self, model: Type[T], prefix: str, expire: int = 3600):
#         self.model = model
#         self.prefix = prefix
#         self.expire = expire

#     async def get_cached_or_db(self, id: str, db_func):
#         """
#         Logic:
#         1. Check Redis for prefix:id
#         2. If found, parse JSON to Pydantic and return
#         3. If not, run db_func, save to Redis, and return
#         """
#         r = await get_redis_client()
#         cache_key = f"{self.prefix}:{id}"

#         # 1. Try Cache
#         cached_data = await r.get(cache_key)
#         if cached_data:
#             return self.model.model_validate_json(cached_data)

#         # 2. Cache Miss: Run the DB query provided as db_func
#         data = await db_func()
#         if data:
#             # 3. Store in Redis for next time
#             await r.setex(cache_key, self.expire, data.model_dump_json())

#         return data

import json

from app.core.redis import redis_client


async def get_cached_object(cache_key: str):
    data = await redis_client.get(cache_key)
    return json.loads(data) if data else None


async def set_cached_object(cache_key: str, data: dict, expire: int = 3600):
    await redis_client.setex(cache_key, expire, json.dumps(data))

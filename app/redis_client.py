import redis.asyncio as aioredis

from app.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

redis_client = aioredis.Redis(
    host=REDIS_HOST,
    port=int(REDIS_PORT),
    db=int(REDIS_DB),
    password=REDIS_PASSWORD or None,
    decode_responses=False,
)


async def get_redis():
    return redis_client
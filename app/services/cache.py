import json
import redis.asyncio as redis


class CacheService:
    def __init__(self, url="redis://localhost:6379/0"):
        self.client = redis.from_url(url, decode_responses=True)

    async def get(self, key: str):
        data = await self.client.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value, ttl: int = 86400):
        await self.client.set(key, json.dumps(value), ex=ttl)

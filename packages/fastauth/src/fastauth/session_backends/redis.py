from __future__ import annotations

import json
from typing import Any

from fastauth._compat import require


class RedisSessionBackend:
    """Redis-backed session backend for production use."""

    def __init__(self, url: str, prefix: str = "fastauth:session:") -> None:
        require("redis", "redis")
        import redis.asyncio as aioredis

        self._redis = aioredis.from_url(url)
        self._prefix = prefix

    def _key(self, session_id: str) -> str:
        return f"{self._prefix}{session_id}"

    async def read(self, session_id: str) -> dict[str, Any] | None:
        data = await self._redis.get(self._key(session_id))
        if data is None:
            return None
        return json.loads(data)

    async def write(self, session_id: str, data: dict[str, Any], ttl: int) -> None:
        await self._redis.setex(self._key(session_id), ttl, json.dumps(data))

    async def delete(self, session_id: str) -> None:
        await self._redis.delete(self._key(session_id))

    async def exists(self, session_id: str) -> bool:
        return await self._redis.exists(self._key(session_id)) > 0

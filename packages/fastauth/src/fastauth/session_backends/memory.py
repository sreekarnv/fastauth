from __future__ import annotations

import time
from typing import Any


class MemorySessionBackend:
    def __init__(self) -> None:
        self._store: dict[str, tuple[dict[str, Any], float]] = {}

    async def read(self, session_id: str) -> dict[str, Any] | None:
        entry = self._store.get(session_id)
        if not entry:
            return None
        data, expires_at = entry
        if time.time() > expires_at:
            del self._store[session_id]
            return None
        return data

    async def write(self, session_id: str, data: dict[str, Any], ttl: int) -> None:
        self._store[session_id] = (data, time.time() + ttl)

    async def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    async def exists(self, session_id: str) -> bool:
        result = await self.read(session_id)
        return result is not None

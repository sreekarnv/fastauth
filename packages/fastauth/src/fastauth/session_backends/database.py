from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastauth.core.protocols import SessionAdapter
from fastauth.types import SessionData


class DatabaseSessionBackend:
    def __init__(self, session_adapter: SessionAdapter) -> None:
        self._adapter = session_adapter

    async def read(self, session_id: str) -> dict[str, Any] | None:
        session = await self._adapter.get_session(session_id)
        if not session:
            return None
        return dict(session)

    async def write(self, session_id: str, data: dict[str, Any], ttl: int) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        session_data: SessionData = {
            "id": session_id,
            "user_id": data["user_id"],
            "expires_at": expires_at,
            "ip_address": data.get("ip_address"),
            "user_agent": data.get("user_agent"),
        }
        await self._adapter.create_session(session_data)

    async def delete(self, session_id: str) -> None:
        await self._adapter.delete_session(session_id)

    async def exists(self, session_id: str) -> bool:
        session = await self._adapter.get_session(session_id)
        return session is not None

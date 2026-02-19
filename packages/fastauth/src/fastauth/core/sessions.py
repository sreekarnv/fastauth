from __future__ import annotations

import json
from typing import Any

from cuid2 import cuid_wrapper

from fastauth.config import FastAuthConfig
from fastauth.core.protocols import SessionBackend, UserAdapter
from fastauth.core.tokens import create_token_pair, decode_token
from fastauth.types import UserData

generate_id = cuid_wrapper()


class JWTSessionStrategy:
    """Stateless JWT-based session strategy."""

    def __init__(self, config: FastAuthConfig, adapter: UserAdapter) -> None:
        self._config = config
        self._adapter = adapter

    async def create(self, user: UserData, **kwargs: Any) -> str:
        pair = create_token_pair(user, self._config)
        return json.dumps(pair)

    async def validate(self, token: str) -> UserData | None:
        try:
            claims = decode_token(token, self._config)
        except Exception:
            return None
        if claims.get("type") != "access":
            return None
        return await self._adapter.get_user_by_id(claims["sub"])

    async def invalidate(self, token: str) -> None:
        # JWT is stateless (can't revoke without a blocklist)
        pass

    async def refresh(self, token: str) -> str | None:
        try:
            claims = decode_token(token, self._config)
        except Exception:
            return None
        if claims.get("type") != "refresh":
            return None
        user = await self._adapter.get_user_by_id(claims["sub"])
        if not user or not user["is_active"]:
            return None
        pair = create_token_pair(user, self._config)
        return json.dumps(pair)


class DatabaseSessionStrategy:
    """Server-side session strategy using a SessionBackend for storage."""

    def __init__(
        self, backend: SessionBackend, adapter: UserAdapter, ttl: int = 86400
    ) -> None:
        self._backend = backend
        self._adapter = adapter
        self._ttl = ttl

    async def create(self, user: UserData, **kwargs: Any) -> str:
        session_id = generate_id()
        data = {"user_id": user["id"], **kwargs}
        await self._backend.write(session_id, data, self._ttl)
        return session_id

    async def validate(self, session_id: str) -> UserData | None:
        data = await self._backend.read(session_id)
        if not data:
            return None
        return await self._adapter.get_user_by_id(data["user_id"])

    async def invalidate(self, session_id: str) -> None:
        await self._backend.delete(session_id)

    async def refresh(self, session_id: str) -> str | None:
        data = await self._backend.read(session_id)
        if not data:
            return None
        await self._backend.write(session_id, data, self._ttl)
        return session_id

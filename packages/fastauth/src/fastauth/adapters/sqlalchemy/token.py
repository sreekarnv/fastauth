from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select

from fastauth.adapters.sqlalchemy.models import TokenModel
from fastauth.types import TokenData


def _to_token_data(token: TokenModel) -> TokenData:
    return {
        "token": token.token,
        "user_id": token.user_id,
        "token_type": token.token_type,
        "expires_at": token.expires_at,
    }


class SQLAlchemyTokenAdapter:
    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    async def create_token(self, token: TokenData) -> TokenData:
        async with self._session_factory() as session:
            model = TokenModel(
                token=token["token"],
                user_id=token["user_id"],
                token_type=token["token_type"],
                expires_at=token["expires_at"],
                created_at=datetime.now(timezone.utc),
            )
            session.add(model)
            await session.commit()
            return token

    async def get_token(self, token: str, token_type: str) -> TokenData | None:
        async with self._session_factory() as session:
            now = datetime.now(timezone.utc)
            result = await session.execute(
                select(TokenModel).where(
                    TokenModel.token == token,
                    TokenModel.token_type == token_type,
                    TokenModel.expires_at > now,
                )
            )
            model = result.scalar_one_or_none()
            return _to_token_data(model) if model else None

    async def delete_token(self, token: str) -> None:
        async with self._session_factory() as session:
            await session.execute(delete(TokenModel).where(TokenModel.token == token))
            await session.commit()

    async def delete_user_tokens(
        self, user_id: str, token_type: str | None = None
    ) -> None:
        async with self._session_factory() as session:
            stmt = delete(TokenModel).where(TokenModel.user_id == user_id)
            if token_type:
                stmt = stmt.where(TokenModel.token_type == token_type)
            await session.execute(stmt)
            await session.commit()

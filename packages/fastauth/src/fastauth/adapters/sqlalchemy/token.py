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
        "raw_data": token.raw_data,
    }


class SQLAlchemyTokenAdapter:
    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    async def create_token(self, token: TokenData) -> TokenData:
        async with self._session_factory() as session:
            raw_data = token["raw_data"] if "raw_data" in token else None
            model = TokenModel(
                token=token["token"],
                user_id=token["user_id"],
                token_type=token["token_type"],
                expires_at=token["expires_at"],
                created_at=datetime.now(timezone.utc),
                raw_data=raw_data,
            )
            await session.merge(model)
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

    async def consume_token(self, token: str, token_type: str) -> TokenData | None:
        """Atomically read and delete a token.

        Reads the row inside a transaction and then issues a conditional
        ``DELETE`` whose row count is inspected to detect concurrent
        consumers. On databases that support row-level locks (PostgreSQL,
        MySQL), the inner transaction is opened with ``SELECT ... FOR
        UPDATE`` so the read and delete run as one atomic step. The final
        ``rowcount`` check ensures that even engines without row-level
        locking (SQLite) still guarantee single-consumer semantics.
        """
        async with self._session_factory() as session:
            now = datetime.now(timezone.utc)
            stmt = (
                select(TokenModel)
                .where(
                    TokenModel.token == token,
                    TokenModel.token_type == token_type,
                    TokenModel.expires_at > now,
                )
                .with_for_update()
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            if model is None:
                await session.rollback()
                return None
            data = _to_token_data(model)
            del_result = await session.execute(
                delete(TokenModel).where(
                    TokenModel.token == token,
                    TokenModel.token_type == token_type,
                )
            )
            if del_result.rowcount == 0:
                # Another consumer committed a delete for this row first
                # (e.g. SQLite where FOR UPDATE is a no-op). Roll back so
                # we don't leak an uncommitted read.
                await session.rollback()
                return None
            await session.commit()
            return data

    async def delete_user_tokens(
        self, user_id: str, token_type: str | None = None
    ) -> None:
        async with self._session_factory() as session:
            stmt = delete(TokenModel).where(TokenModel.user_id == user_id)
            if token_type:
                stmt = stmt.where(TokenModel.token_type == token_type)
            await session.execute(stmt)
            await session.commit()

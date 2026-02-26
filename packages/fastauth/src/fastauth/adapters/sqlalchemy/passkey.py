from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select, update

from fastauth.adapters.sqlalchemy.models import PasskeyModel
from fastauth.types import PasskeyData


def _to_passkey_data(model: PasskeyModel) -> PasskeyData:
    return {
        "id": model.id,
        "user_id": model.user_id,
        "public_key": model.public_key,
        "sign_count": model.sign_count,
        "aaguid": model.aaguid,
        "name": model.name,
        "created_at": model.created_at.isoformat(),
        "last_used_at": model.last_used_at.isoformat() if model.last_used_at else None,
    }


class SQLAlchemyPasskeyAdapter:
    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    async def create_passkey(
        self,
        user_id: str,
        credential_id: str,
        public_key: bytes,
        sign_count: int,
        aaguid: str,
        name: str,
    ) -> PasskeyData:
        async with self._session_factory() as session:
            model = PasskeyModel(
                id=credential_id,
                user_id=user_id,
                public_key=public_key,
                sign_count=sign_count,
                aaguid=aaguid,
                name=name,
                created_at=datetime.now(timezone.utc),
                last_used_at=None,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return _to_passkey_data(model)

    async def get_passkey(self, credential_id: str) -> PasskeyData | None:
        async with self._session_factory() as session:
            stmt = select(PasskeyModel).where(PasskeyModel.id == credential_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return _to_passkey_data(model) if model else None

    async def get_passkeys_by_user(self, user_id: str) -> list[PasskeyData]:
        async with self._session_factory() as session:
            stmt = select(PasskeyModel).where(PasskeyModel.user_id == user_id)
            result = await session.execute(stmt)
            return [_to_passkey_data(m) for m in result.scalars().all()]

    async def update_sign_count(
        self, credential_id: str, sign_count: int, last_used_at: str
    ) -> None:
        async with self._session_factory() as session:
            stmt = (
                update(PasskeyModel)
                .where(PasskeyModel.id == credential_id)
                .values(
                    sign_count=sign_count,
                    last_used_at=datetime.fromisoformat(last_used_at),
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def delete_passkey(self, credential_id: str) -> None:
        async with self._session_factory() as session:
            stmt = delete(PasskeyModel).where(PasskeyModel.id == credential_id)
            await session.execute(stmt)
            await session.commit()

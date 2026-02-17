from __future__ import annotations

from datetime import datetime, timezone

from cuid2 import cuid_wrapper
from sqlalchemy import delete, select

from fastauth.adapters.sqlalchemy.models import OAuthAccountModel
from fastauth.types import OAuthAccountData

generate_id = cuid_wrapper()


def _to_oauth_data(model: OAuthAccountModel) -> OAuthAccountData:
    return {
        "provider": model.provider,
        "provider_account_id": model.provider_account_id,
        "user_id": model.user_id,
        "access_token": model.access_token,
        "refresh_token": model.refresh_token,
        "expires_at": model.expires_at,
    }


class SQLAlchemyOAuthAccountAdapter:
    def __init__(self, session_factory: object) -> None:
        self._session_factory = session_factory

    async def create_oauth_account(
        self, account: OAuthAccountData
    ) -> OAuthAccountData:
        async with self._session_factory() as session:
            model = OAuthAccountModel(
                id=generate_id(),
                provider=account["provider"],
                provider_account_id=account["provider_account_id"],
                user_id=account["user_id"],
                access_token=account.get("access_token"),
                refresh_token=account.get("refresh_token"),
                expires_at=account.get("expires_at"),
                created_at=datetime.now(timezone.utc),
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return _to_oauth_data(model)

    async def get_oauth_account(
        self, provider: str, provider_account_id: str
    ) -> OAuthAccountData | None:
        async with self._session_factory() as session:
            stmt = select(OAuthAccountModel).where(
                OAuthAccountModel.provider == provider,
                OAuthAccountModel.provider_account_id
                == provider_account_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return _to_oauth_data(model) if model else None

    async def get_user_oauth_accounts(
        self, user_id: str
    ) -> list[OAuthAccountData]:
        async with self._session_factory() as session:
            stmt = select(OAuthAccountModel).where(
                OAuthAccountModel.user_id == user_id
            )
            result = await session.execute(stmt)
            return [_to_oauth_data(m) for m in result.scalars().all()]

    async def delete_oauth_account(
        self, provider: str, provider_account_id: str
    ) -> None:
        async with self._session_factory() as session:
            stmt = delete(OAuthAccountModel).where(
                OAuthAccountModel.provider == provider,
                OAuthAccountModel.provider_account_id
                == provider_account_id,
            )
            await session.execute(stmt)
            await session.commit()

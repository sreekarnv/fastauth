"""
SQLAlchemy OAuth account adapter implementation.

Provides database operations for OAuth account management using SQLAlchemy/SQLModel.
"""

import uuid
from datetime import UTC, datetime

from sqlmodel import Session, select

from fastauth.adapters.base.oauth_accounts import OAuthAccountAdapter
from fastauth.adapters.sqlalchemy.models import OAuthAccount


class SQLAlchemyOAuthAccountAdapter(OAuthAccountAdapter):
    """
    SQLAlchemy implementation of OAuthAccountAdapter.
    """

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        user_id: uuid.UUID,
        provider: str,
        provider_user_id: str,
        access_token_hash: str,
        refresh_token_hash: str | None = None,
        expires_at: datetime | None = None,
        email: str | None = None,
        name: str | None = None,
        avatar_url: str | None = None,
    ):
        account = OAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            access_token_hash=access_token_hash,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            email=email,
            name=name,
            avatar_url=avatar_url,
        )
        self.session.add(account)
        self.session.commit()
        self.session.refresh(account)
        return account

    def get_by_provider_user_id(self, *, provider: str, provider_user_id: str):
        return self.session.exec(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
        ).first()

    def get_by_user_id(self, *, user_id: uuid.UUID, provider: str | None = None):
        statement = select(OAuthAccount).where(OAuthAccount.user_id == user_id)
        if provider:
            statement = statement.where(OAuthAccount.provider == provider)
        return list(self.session.exec(statement).all())

    def update_tokens(
        self,
        *,
        account_id: uuid.UUID,
        access_token_hash: str,
        refresh_token_hash: str | None = None,
        expires_at: datetime | None = None,
    ) -> None:
        account = self.session.get(OAuthAccount, account_id)
        if not account:
            return

        account.access_token_hash = access_token_hash
        account.refresh_token_hash = refresh_token_hash
        account.expires_at = expires_at
        account.updated_at = datetime.now(UTC)

        self.session.add(account)
        self.session.commit()

    def delete(self, *, account_id: uuid.UUID) -> None:
        account = self.session.get(OAuthAccount, account_id)
        if account:
            self.session.delete(account)
            self.session.commit()

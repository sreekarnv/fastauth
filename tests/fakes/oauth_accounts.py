import uuid
from datetime import UTC, datetime

from fastauth.adapters.base.oauth_accounts import OAuthAccountAdapter


class FakeOAuthAccount:
    def __init__(
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
        self.id = uuid.uuid4()
        self.user_id = user_id
        self.provider = provider
        self.provider_user_id = provider_user_id
        self.access_token_hash = access_token_hash
        self.refresh_token_hash = refresh_token_hash
        self.expires_at = expires_at
        self.email = email
        self.name = name
        self.avatar_url = avatar_url
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)


class FakeOAuthAccountAdapter(OAuthAccountAdapter):
    def __init__(self):
        self.accounts = {}  # account_id -> FakeOAuthAccount

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
        account = FakeOAuthAccount(
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
        self.accounts[account.id] = account
        return account

    def get_by_provider_user_id(self, *, provider: str, provider_user_id: str):
        for account in self.accounts.values():
            if (
                account.provider == provider
                and account.provider_user_id == provider_user_id
            ):
                return account
        return None

    def get_by_user_id(self, *, user_id: uuid.UUID, provider: str | None = None):
        accounts = []
        for account in self.accounts.values():
            if account.user_id == user_id:
                if provider is None or account.provider == provider:
                    accounts.append(account)
        return accounts

    def update_tokens(
        self,
        *,
        account_id: uuid.UUID,
        access_token_hash: str,
        refresh_token_hash: str | None = None,
        expires_at: datetime | None = None,
    ) -> None:
        account = self.accounts.get(account_id)
        if account:
            account.access_token_hash = access_token_hash
            account.refresh_token_hash = refresh_token_hash
            account.expires_at = expires_at
            account.updated_at = datetime.now(UTC)

    def delete(self, *, account_id: uuid.UUID) -> None:
        if account_id in self.accounts:
            del self.accounts[account_id]

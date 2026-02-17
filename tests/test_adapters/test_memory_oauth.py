from fastauth.adapters.memory import MemoryOAuthAccountAdapter
from fastauth.types import OAuthAccountData


def _make_account(
    provider: str = "google",
    provider_account_id: str = "123",
    user_id: str = "u1",
) -> OAuthAccountData:
    return OAuthAccountData(
        provider=provider,
        provider_account_id=provider_account_id,
        user_id=user_id,
        access_token="tok",
        refresh_token="ref",
        expires_at=None,
    )


async def test_create_and_get():
    adapter = MemoryOAuthAccountAdapter()
    account = _make_account()
    result = await adapter.create_oauth_account(account)
    assert result["provider"] == "google"

    fetched = await adapter.get_oauth_account("google", "123")
    assert fetched is not None
    assert fetched["user_id"] == "u1"


async def test_get_nonexistent():
    adapter = MemoryOAuthAccountAdapter()
    assert await adapter.get_oauth_account("google", "missing") is None


async def test_get_user_accounts():
    adapter = MemoryOAuthAccountAdapter()
    await adapter.create_oauth_account(_make_account("google", "g1", "u1"))
    await adapter.create_oauth_account(_make_account("github", "gh1", "u1"))
    await adapter.create_oauth_account(_make_account("google", "g2", "u2"))

    accounts = await adapter.get_user_oauth_accounts("u1")
    assert len(accounts) == 2
    providers = {a["provider"] for a in accounts}
    assert providers == {"google", "github"}


async def test_delete():
    adapter = MemoryOAuthAccountAdapter()
    await adapter.create_oauth_account(_make_account())
    await adapter.delete_oauth_account("google", "123")
    assert await adapter.get_oauth_account("google", "123") is None


async def test_delete_nonexistent():
    adapter = MemoryOAuthAccountAdapter()
    await adapter.delete_oauth_account("google", "missing")  # no error

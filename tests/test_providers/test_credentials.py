import pytest
from fastauth.adapters.memory import MemoryTokenAdapter, MemoryUserAdapter
from fastauth.core.credentials import hash_password
from fastauth.exceptions import AccountLockedError, AuthenticationError
from fastauth.providers.credentials import CredentialsProvider


def test_account_locked_error_without_locked_until():
    err = AccountLockedError()
    assert "Too many failed login attempts" in str(err)


def test_account_locked_error_with_locked_until():
    err = AccountLockedError(locked_until=120)
    assert "2 minutes" in str(err)


@pytest.fixture
def user_adapter():
    return MemoryUserAdapter()


@pytest.fixture
def token_adapter():
    return MemoryTokenAdapter()


@pytest.fixture
def provider():
    return CredentialsProvider(max_login_attempts=3, lockout_duration=60)


@pytest.mark.asyncio
async def test_successful_login(user_adapter, token_adapter, provider):
    hashed = hash_password("password123")
    _ = await user_adapter.create_user("test@example.com", hashed)

    result = await provider.authenticate(
        user_adapter, "test@example.com", "password123", token_adapter
    )
    assert result["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_invalid_email(user_adapter, token_adapter, provider):
    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        await provider.authenticate(
            user_adapter, "nonexistent@example.com", "password", token_adapter
        )


@pytest.mark.asyncio
async def test_invalid_password(user_adapter, token_adapter, provider):
    hashed = hash_password("password123")
    await user_adapter.create_user("test@example.com", hashed)

    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        await provider.authenticate(
            user_adapter, "test@example.com", "wrong_password", token_adapter
        )


@pytest.mark.asyncio
async def test_inactive_user(user_adapter, token_adapter, provider):
    hashed = hash_password("password123")
    _ = await user_adapter.create_user("test@example.com", hashed, is_active=False)

    with pytest.raises(AuthenticationError, match="Account is deactivated"):
        await provider.authenticate(
            user_adapter, "test@example.com", "password123", token_adapter
        )


@pytest.mark.asyncio
async def test_account_lockout_after_max_attempts(
    user_adapter, token_adapter, provider
):
    hashed = hash_password("password123")
    _ = await user_adapter.create_user("test@example.com", hashed)

    for _ in range(3):
        with pytest.raises(AuthenticationError):
            await provider.authenticate(
                user_adapter, "test@example.com", "wrong", token_adapter
            )

    with pytest.raises(AccountLockedError):
        await provider.authenticate(
            user_adapter, "test@example.com", "password123", token_adapter
        )


@pytest.mark.asyncio
async def test_successful_login_clears_attempts(user_adapter, token_adapter, provider):
    hashed = hash_password("password123")
    user = await user_adapter.create_user("test@example.com", hashed)

    with pytest.raises(AuthenticationError):
        await provider.authenticate(
            user_adapter, "test@example.com", "wrong", token_adapter
        )

    result = await provider.authenticate(
        user_adapter, "test@example.com", "password123", token_adapter
    )
    assert result["email"] == "test@example.com"

    attempt = await token_adapter.get_token(
        f"login_attempt:{user['id']}", "login_attempt"
    )
    assert attempt is None


@pytest.mark.asyncio
async def test_login_without_token_adapter(user_adapter, provider):
    hashed = hash_password("password123")
    await user_adapter.create_user("test@example.com", hashed)

    result = await provider.authenticate(
        user_adapter, "test@example.com", "password123", None
    )
    assert result["email"] == "test@example.com"

import pytest
from fastauth.core.protocols import EventHooks


@pytest.fixture
def hooks():
    return EventHooks()


@pytest.fixture
def user():
    return {"id": "u1", "email": "a@b.com", "is_active": True, "email_verified": False}


async def test_on_signup(hooks, user):
    await hooks.on_signup(user)


async def test_on_signin(hooks, user):
    await hooks.on_signin(user, "credentials")


async def test_on_signout(hooks, user):
    await hooks.on_signout(user)


async def test_on_token_refresh(hooks, user):
    await hooks.on_token_refresh(user)


async def test_on_email_verify(hooks, user):
    await hooks.on_email_verify(user)


async def test_on_password_reset(hooks, user):
    await hooks.on_password_reset(user)


async def test_on_oauth_link(hooks, user):
    await hooks.on_oauth_link(user, "google")


async def test_allow_signin_returns_true(hooks, user):
    result = await hooks.allow_signin(user, "credentials")
    assert result is True


async def test_modify_session_returns_session(hooks, user):
    session = {"key": "value", "extra": 123}
    result = await hooks.modify_session(session, user)
    assert result == session


async def test_modify_jwt_returns_token(hooks, user):
    token = {"type": "access", "sub": "u1"}
    result = await hooks.modify_jwt(token, user)
    assert result == token

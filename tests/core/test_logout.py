from fastauth.core.refresh_tokens import (
    create_refresh_token,
    revoke_refresh_token,
)

from fastauth.core.users import create_user
from tests.fakes.users import FakeUserAdapter
from tests.fakes.refresh_tokens import FakeRefreshTokenAdapter


def test_logout_revokes_refresh_token():
    users = FakeUserAdapter()
    refresh_tokens = FakeRefreshTokenAdapter()

    user = create_user(
        users=users,
        email="test@example.com",
        password="secret",
    )

    raw_token = create_refresh_token(
        refresh_tokens=refresh_tokens,
        user_id=user.id,
    )

    revoke_refresh_token(
        refresh_tokens=refresh_tokens,
        token=raw_token,
    )

    token_hash = next(iter(refresh_tokens.tokens.keys()))
    token = refresh_tokens.tokens[token_hash]

    assert token.revoked is True

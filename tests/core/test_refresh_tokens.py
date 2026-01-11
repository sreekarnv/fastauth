"""Tests for refresh token operations."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from fastauth.core.refresh_tokens import (
    RefreshTokenError,
    rotate_refresh_token,
)
from tests.fakes.refresh_tokens import FakeRefreshTokenAdapter


@pytest.fixture
def refresh_tokens():
    return FakeRefreshTokenAdapter()


def test_rotate_refresh_token_expired(refresh_tokens):
    """Test that expired refresh tokens raise an error during rotation."""
    from fastauth.security.tokens import generate_secure_token, hash_token

    token = generate_secure_token(48)
    token_hash = hash_token(token)
    user_id = uuid.uuid4()

    refresh_tokens.create(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    record = next(iter(refresh_tokens.tokens.values()))
    record.expires_at = datetime.now(UTC) - timedelta(minutes=1)

    with pytest.raises(RefreshTokenError, match="Refresh token expired"):
        rotate_refresh_token(
            refresh_tokens=refresh_tokens,
            token=token,
        )

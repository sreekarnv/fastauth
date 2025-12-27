from datetime import timedelta

import pytest

from fastauth.security.jwt import (
    TokenError,
    create_access_token,
    decode_access_token,
)


def test_create_and_decode_access_token():
    token = create_access_token(subject="user-id-123")

    payload = decode_access_token(token)

    assert payload["sub"] == "user-id-123"
    assert "exp" in payload
    assert "iat" in payload


def test_expired_token_raises_error():
    token = create_access_token(
        subject="user-id-123",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(TokenError):
        decode_access_token(token)

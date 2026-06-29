from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from fastauth.core.one_time_tokens import (
    generate_one_time_token,
    hash_one_time_token,
)
from fastauth.exceptions import AuthenticationError
from fastauth.types import UserData

if TYPE_CHECKING:
    from fastauth.app import FastAuth


class MagicLinksProvider:
    id = "magic_links"
    name = "Magic Links"
    auth_type = "magic_links"

    def __init__(self, max_age: int = 15 * 60) -> None:
        self.max_age = max_age

    async def send_login_request(self, fa: "FastAuth", user: UserData) -> None:
        assert fa.config.token_adapter is not None

        raw_token = generate_one_time_token()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.max_age)

        await fa.config.token_adapter.create_token(
            {
                "expires_at": expires_at,
                "token": hash_one_time_token(raw_token),
                "token_type": "magic_link_login_request",
                "raw_data": None,
                "user_id": user["id"],
            }
        )

        if fa.email_dispatcher:
            await fa.email_dispatcher.send_magic_link_login_request(
                user=user, token=raw_token
            )

    async def authenticate(self, fa: "FastAuth", token: str) -> UserData:
        assert fa.config.token_adapter is not None

        token_hash = hash_one_time_token(token)
        _token = await fa.config.token_adapter.get_token(
            token_hash, token_type="magic_link_login_request"
        )

        if not _token:
            raise AuthenticationError("Invalid or expired magic link")

        user = await fa.config.adapter.get_user_by_id(_token["user_id"])

        if not user:
            raise AuthenticationError("Invalid or expired magic link")

        await fa.config.token_adapter.delete_token(token_hash)

        return user

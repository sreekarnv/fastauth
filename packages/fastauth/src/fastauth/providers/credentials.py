from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastauth.core.credentials import verify_password
from fastauth.core.protocols import TokenAdapter, UserAdapter
from fastauth.exceptions import AccountLockedError, AuthenticationError
from fastauth.types import UserData


class CredentialsProvider:
    """Email/password provider using Argon2/bcrypt hashing."""

    id = "credentials"
    name = "Credentials"
    type = "credentials"

    def __init__(
        self,
        max_login_attempts: int = 5,
        lockout_duration: int = 300,
    ) -> None:
        self.max_login_attempts = max_login_attempts
        self.lockout_duration = lockout_duration

    async def authenticate(
        self,
        adapter: UserAdapter,
        email: str,
        password: str,
        token_adapter: TokenAdapter | None = None,
    ) -> UserData:
        user = await adapter.get_user_by_email(email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if token_adapter:
            await self._check_lockout(token_adapter, user["id"])

        hashed = await adapter.get_hashed_password(user["id"])
        if not hashed or not verify_password(password, hashed):
            if token_adapter:
                await self._record_failed_attempt(token_adapter, user["id"])
            raise AuthenticationError("Invalid email or password")

        if not user["is_active"]:
            raise AuthenticationError("Account is deactivated")

        if token_adapter:
            await self._clear_failed_attempts(token_adapter, user["id"])

        return user

    async def _check_lockout(self, token_adapter: TokenAdapter, user_id: str) -> None:
        attempt = await token_adapter.get_token(
            f"login_attempt:{user_id}", "login_attempt"
        )
        if attempt and attempt.get("locked_until"):
            locked_until = attempt["locked_until"]
            if locked_until > datetime.now(timezone.utc):
                raise AccountLockedError(
                    int((locked_until - datetime.now(timezone.utc)).total_seconds())
                )

    async def _record_failed_attempt(
        self, token_adapter: TokenAdapter, user_id: str
    ) -> None:
        attempt = await token_adapter.get_token(
            f"login_attempt:{user_id}", "login_attempt"
        )

        now = datetime.now(timezone.utc)
        if attempt and attempt.get("attempts"):
            attempts = attempt["attempts"] + 1
        else:
            attempts = 1

        if attempts >= self.max_login_attempts:
            locked_until = now + timedelta(seconds=self.lockout_duration)
            await token_adapter.create_token(
                {
                    "token": f"login_attempt:{user_id}",
                    "user_id": user_id,
                    "token_type": "login_attempt",
                    "expires_at": locked_until,
                    "raw_data": {
                        "attempts": attempts,
                        "locked_until": locked_until,
                    },
                }
            )
        else:
            await token_adapter.create_token(
                {
                    "token": f"login_attempt:{user_id}",
                    "user_id": user_id,
                    "token_type": "login_attempt",
                    "expires_at": now + timedelta(minutes=15),
                    "raw_data": {
                        "attempts": attempts,
                        "last_attempt_at": now,
                    },
                }
            )

    async def _clear_failed_attempts(
        self, token_adapter: TokenAdapter, user_id: str
    ) -> None:
        await token_adapter.delete_token(f"login_attempt:{user_id}")

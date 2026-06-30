from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import TYPE_CHECKING

from fastauth.core.credentials import verify_password
from fastauth.core.identity import normalize_email
from fastauth.core.protocols import TokenAdapter, UserAdapter
from fastauth.exceptions import AccountLockedError, AuthenticationError
from fastauth.types import UserData

if TYPE_CHECKING:
    from fastauth.config import SecurityConfig


class CredentialsProvider:
    """Email/password provider using Argon2/bcrypt hashing."""

    id = "credentials"
    name = "Credentials"
    auth_type = "credentials"

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
        security: "SecurityConfig | None" = None,
    ) -> UserData:
        max_attempts = (
            security.max_login_attempts if security else self.max_login_attempts
        )
        lockout_seconds = (
            security.lockout_duration if security else self.lockout_duration
        )

        user = await adapter.get_user_by_email(normalize_email(email))
        if not user:
            raise AuthenticationError("Invalid email or password")

        if token_adapter:
            await self._check_lockout(token_adapter, user["id"], lockout_seconds)

        hashed = await adapter.get_hashed_password(user["id"])
        if not hashed or not verify_password(password, hashed):
            if token_adapter:
                await self._record_failed_attempt(
                    token_adapter, user["id"], max_attempts, lockout_seconds
                )
            raise AuthenticationError("Invalid email or password")

        if not user["is_active"]:
            raise AuthenticationError("Account is deactivated")

        if token_adapter:
            await self._clear_failed_attempts(token_adapter, user["id"])

        return user

    async def _check_lockout(
        self, token_adapter: TokenAdapter, user_id: str, lockout_seconds: int
    ) -> None:
        attempt = await token_adapter.get_token(
            f"login_attempt:{user_id}", "login_attempt"
        )
        raw_data = attempt.get("raw_data") if attempt else None
        if raw_data and raw_data.get("locked_until"):
            locked_until = raw_data["locked_until"]
            if locked_until > datetime.now(timezone.utc):
                raise AccountLockedError(
                    int((locked_until - datetime.now(timezone.utc)).total_seconds())
                )

    async def _record_failed_attempt(
        self,
        token_adapter: TokenAdapter,
        user_id: str,
        max_attempts: int,
        lockout_seconds: int,
    ) -> None:
        attempt = await token_adapter.get_token(
            f"login_attempt:{user_id}", "login_attempt"
        )

        now = datetime.now(timezone.utc)
        raw_data = attempt.get("raw_data") if attempt else None
        attempt_ids = list(raw_data.get("attempt_ids", [])) if raw_data else []
        if raw_data and raw_data.get("attempts") and not attempt_ids:
            attempt_ids = [""] * int(raw_data["attempts"])

        attempt_id = token_urlsafe(16)
        if attempt_id not in attempt_ids:
            attempt_ids.append(attempt_id)

        await self._write_failed_attempt(
            token_adapter,
            user_id,
            attempt_ids,
            max_attempts,
            lockout_seconds,
            now,
        )

        stored = await token_adapter.get_token(
            f"login_attempt:{user_id}", "login_attempt"
        )
        stored_raw_data = stored.get("raw_data") if stored else None
        stored_attempt_ids = (
            list(stored_raw_data.get("attempt_ids", [])) if stored_raw_data else []
        )
        if attempt_id not in stored_attempt_ids:
            merged_ids = [*stored_attempt_ids, attempt_id]
            await self._write_failed_attempt(
                token_adapter,
                user_id,
                merged_ids,
                max_attempts,
                lockout_seconds,
                now,
            )

    async def _write_failed_attempt(
        self,
        token_adapter: TokenAdapter,
        user_id: str,
        attempt_ids: list[str],
        max_attempts: int,
        lockout_seconds: int,
        now: datetime,
    ) -> None:
        attempts = len(attempt_ids)
        raw_data: dict[str, object] = {
            "attempts": attempts,
            "attempt_ids": attempt_ids,
        }
        if attempts >= max_attempts:
            expires_at = now + timedelta(seconds=lockout_seconds)
            raw_data["locked_until"] = expires_at
        else:
            expires_at = now + timedelta(minutes=15)
            raw_data["last_attempt_at"] = now

        await token_adapter.create_token(
            {
                "token": f"login_attempt:{user_id}",
                "user_id": user_id,
                "token_type": "login_attempt",
                "expires_at": expires_at,
                "raw_data": raw_data,
            }
        )

    async def _clear_failed_attempts(
        self, token_adapter: TokenAdapter, user_id: str
    ) -> None:
        await token_adapter.delete_token(f"login_attempt:{user_id}")

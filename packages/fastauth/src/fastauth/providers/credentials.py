from __future__ import annotations

from fastauth.core.credentials import verify_password
from fastauth.core.protocols import UserAdapter
from fastauth.exceptions import AuthenticationError
from fastauth.types import UserData


class CredentialsProvider:
    """Email/password provider using Argon2/bcrypt hashing."""

    id = "credentials"
    name = "Credentials"
    type = "credentials"

    async def authenticate(
        self, adapter: UserAdapter, email: str, password: str
    ) -> UserData:
        user = await adapter.get_user_by_email(email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        hashed = await adapter.get_hashed_password(user["id"])
        if not hashed or not verify_password(password, hashed):
            raise AuthenticationError("Invalid email or password")

        if not user["is_active"]:
            raise AuthenticationError("Account is deactivated")

        return user

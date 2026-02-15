from __future__ import annotations

from datetime import datetime, timezone

from cuid2 import cuid_wrapper

from fastauth.exceptions import UserAlreadyExistsError, UserNotFoundError
from fastauth.types import TokenData, UserData

generate_id = cuid_wrapper()


class MemoryUserAdapter:
    def __init__(self) -> None:
        self._users: dict[str, UserData] = {}
        self._passwords: dict[str, str | None] = {}
        self._email_index: dict[str, str] = {}

    async def create_user(
        self, email: str, hashed_password: str | None = None, **kwargs: str | None
    ) -> UserData:
        if email in self._email_index:
            raise UserAlreadyExistsError(f"User with email '{email}' already exists")

        user_id = generate_id()
        user: UserData = {
            "id": user_id,
            "email": email,
            "name": kwargs.get("name"),
            "image": kwargs.get("image"),
            "email_verified": False,
            "is_active": True,
        }
        self._users[user_id] = user
        self._passwords[user_id] = hashed_password
        self._email_index[email] = user_id
        return user

    async def get_user_by_id(self, user_id: str) -> UserData | None:
        return self._users.get(user_id)

    async def get_user_by_email(self, email: str) -> UserData | None:
        user_id = self._email_index.get(email)
        if user_id is None:
            return None
        return self._users.get(user_id)

    async def update_user(self, user_id: str, **kwargs: str | bool | None) -> UserData:
        user = self._users.get(user_id)
        if not user:
            raise UserNotFoundError(f"User '{user_id}' not found")

        for key, value in kwargs.items():
            if key in user:
                user[key] = value  # type: ignore[literal-required]

        if "email" in kwargs and kwargs["email"] != user["email"]:
            old_email = user["email"]
            del self._email_index[old_email]
            self._email_index[kwargs["email"]] = user_id  # type: ignore[index]

        self._users[user_id] = user
        return user

    async def delete_user(self, user_id: str, soft: bool = True) -> None:
        user = self._users.get(user_id)
        if not user:
            raise UserNotFoundError(f"User '{user_id}' not found")

        if soft:
            user["is_active"] = False
            self._users[user_id] = user
        else:
            del self._email_index[user["email"]]
            del self._users[user_id]
            self._passwords.pop(user_id, None)

    async def get_hashed_password(self, user_id: str) -> str | None:
        return self._passwords.get(user_id)

    async def set_hashed_password(self, user_id: str, hashed_password: str) -> None:
        if user_id not in self._users:
            raise UserNotFoundError(f"User '{user_id}' not found")
        self._passwords[user_id] = hashed_password


class MemoryTokenAdapter:
    def __init__(self) -> None:
        self._tokens: dict[str, TokenData] = {}

    async def create_token(self, token: TokenData) -> TokenData:
        self._tokens[token["token"]] = token
        return token

    async def get_token(self, token: str, token_type: str) -> TokenData | None:
        stored = self._tokens.get(token)
        if stored is None:
            return None
        if stored["token_type"] != token_type:
            return None
        if stored["expires_at"] < datetime.now(timezone.utc):
            del self._tokens[token]
            return None
        return stored

    async def delete_token(self, token: str) -> None:
        self._tokens.pop(token, None)

    async def delete_user_tokens(
        self, user_id: str, token_type: str | None = None
    ) -> None:
        to_delete = [
            key
            for key, t in self._tokens.items()
            if t["user_id"] == user_id
            and (token_type is None or t["token_type"] == token_type)
        ]
        for key in to_delete:
            del self._tokens[key]

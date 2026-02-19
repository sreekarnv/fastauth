from __future__ import annotations

from datetime import datetime, timezone

from cuid2 import cuid_wrapper

from fastauth.core.protocols import UserAdapter
from fastauth.exceptions import UserAlreadyExistsError, UserNotFoundError
from fastauth.types import (
    OAuthAccountData,
    RoleData,
    SessionData,
    TokenData,
    UserData,
)

generate_id = cuid_wrapper()


class MemoryUserAdapter(UserAdapter):
    """In-memory user adapter for testing."""

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
    """In-memory one-time token adapter for testing."""

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


class MemorySessionAdapter:
    """In-memory session adapter for testing."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionData] = {}

    async def create_session(self, session: SessionData) -> SessionData:
        self._sessions[session["id"]] = session
        return session

    async def get_session(self, session_id: str) -> SessionData | None:
        session = self._sessions.get(session_id)
        if not session:
            return None
        if session["expires_at"] < datetime.now(timezone.utc):
            del self._sessions[session_id]
            return None
        return session

    async def delete_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def delete_user_sessions(self, user_id: str) -> None:
        to_delete = [
            sid for sid, s in self._sessions.items() if s["user_id"] == user_id
        ]
        for sid in to_delete:
            del self._sessions[sid]

    async def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        expired = [sid for sid, s in self._sessions.items() if s["expires_at"] < now]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)


class MemoryRoleAdapter:
    """In-memory RBAC adapter for testing."""

    def __init__(self) -> None:
        self._roles: dict[str, RoleData] = {}
        self._user_roles: dict[str, set[str]] = {}

    async def create_role(
        self, name: str, permissions: list[str] | None = None
    ) -> RoleData:
        role: RoleData = {
            "name": name,
            "permissions": permissions or [],
        }
        self._roles[name] = role
        return role

    async def get_role(self, name: str) -> RoleData | None:
        return self._roles.get(name)

    async def list_roles(self) -> list[RoleData]:
        return list(self._roles.values())

    async def delete_role(self, name: str) -> None:
        self._roles.pop(name, None)
        for user_roles in self._user_roles.values():
            user_roles.discard(name)

    async def add_permissions(self, role_name: str, permissions: list[str]) -> None:
        role = self._roles.get(role_name)
        if role:
            existing = set(role["permissions"])
            existing.update(permissions)
            role["permissions"] = list(existing)

    async def remove_permissions(self, role_name: str, permissions: list[str]) -> None:
        role = self._roles.get(role_name)
        if role:
            existing = set(role["permissions"])
            existing -= set(permissions)
            role["permissions"] = list(existing)

    async def assign_role(self, user_id: str, role_name: str) -> None:
        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()
        self._user_roles[user_id].add(role_name)

    async def revoke_role(self, user_id: str, role_name: str) -> None:
        if user_id in self._user_roles:
            self._user_roles[user_id].discard(role_name)

    async def get_user_roles(self, user_id: str) -> list[str]:
        return list(self._user_roles.get(user_id, set()))

    async def get_user_permissions(self, user_id: str) -> set[str]:
        roles = self._user_roles.get(user_id, set())
        permissions: set[str] = set()
        for role_name in roles:
            role = self._roles.get(role_name)
            if role:
                permissions.update(role["permissions"])
        return permissions


class MemoryOAuthAccountAdapter:
    """In-memory OAuth account adapter for testing."""

    def __init__(self) -> None:
        self._accounts: dict[tuple[str, str], OAuthAccountData] = {}

    async def create_oauth_account(self, account: OAuthAccountData) -> OAuthAccountData:
        key = (account["provider"], account["provider_account_id"])
        self._accounts[key] = account
        return account

    async def get_oauth_account(
        self, provider: str, provider_account_id: str
    ) -> OAuthAccountData | None:
        return self._accounts.get((provider, provider_account_id))

    async def get_user_oauth_accounts(self, user_id: str) -> list[OAuthAccountData]:
        return [a for a in self._accounts.values() if a["user_id"] == user_id]

    async def delete_oauth_account(
        self, provider: str, provider_account_id: str
    ) -> None:
        self._accounts.pop((provider, provider_account_id), None)

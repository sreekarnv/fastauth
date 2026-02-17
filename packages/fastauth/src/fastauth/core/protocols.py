from __future__ import annotations

from typing import Any, Literal, Protocol

from fastauth.types import OAuthAccountData, RoleData, SessionData, TokenData, UserData


class UserAdapter(Protocol):
    async def create_user(
        self, email: str, hashed_password: str | None = None, **kwargs: Any
    ) -> UserData: ...

    async def get_user_by_id(self, user_id: str) -> UserData | None: ...

    async def get_user_by_email(self, email: str) -> UserData | None: ...

    async def update_user(self, user_id: str, **kwargs: Any) -> UserData: ...

    async def delete_user(self, user_id: str, soft: bool = True) -> None: ...

    async def get_hashed_password(self, user_id: str) -> str | None: ...

    async def set_hashed_password(self, user_id: str, hashed_password: str) -> None: ...


class SessionAdapter(Protocol):
    async def create_session(self, session: SessionData) -> SessionData: ...

    async def get_session(self, session_id: str) -> SessionData | None: ...

    async def delete_session(self, session_id: str) -> None: ...

    async def delete_user_sessions(self, user_id: str) -> None: ...

    async def cleanup_expired(self) -> int: ...


class TokenAdapter(Protocol):
    async def create_token(self, token: TokenData) -> TokenData: ...

    async def get_token(self, token: str, token_type: str) -> TokenData | None: ...

    async def delete_token(self, token: str) -> None: ...

    async def delete_user_tokens(
        self, user_id: str, token_type: str | None = None
    ) -> None: ...


class OAuthAccountAdapter(Protocol):
    async def create_oauth_account(
        self, account: OAuthAccountData
    ) -> OAuthAccountData: ...

    async def get_oauth_account(
        self, provider: str, provider_account_id: str
    ) -> OAuthAccountData | None: ...

    async def get_user_oauth_accounts(self, user_id: str) -> list[OAuthAccountData]: ...

    async def delete_oauth_account(
        self, provider: str, provider_account_id: str
    ) -> None: ...


class RoleAdapter(Protocol):
    async def create_role(
        self, name: str, permissions: list[str] | None = None
    ) -> RoleData: ...

    async def get_role(self, name: str) -> RoleData | None: ...

    async def list_roles(self) -> list[RoleData]: ...

    async def delete_role(self, name: str) -> None: ...

    async def add_permissions(self, role_name: str, permissions: list[str]) -> None: ...

    async def remove_permissions(
        self, role_name: str, permissions: list[str]
    ) -> None: ...

    async def assign_role(self, user_id: str, role_name: str) -> None: ...

    async def revoke_role(self, user_id: str, role_name: str) -> None: ...

    async def get_user_roles(self, user_id: str) -> list[str]: ...

    async def get_user_permissions(self, user_id: str) -> set[str]: ...


class AuthProvider(Protocol):
    id: str
    name: str
    auth_type: Literal["oauth", "credentials", "email"]


class OAuthProvider(AuthProvider, Protocol):
    auth_type: str

    async def get_authorization_url(
        self, state: str, redirect_uri: str, **kwargs: Any
    ) -> str: ...

    async def exchange_code(
        self, code: str, redirect_uri: str, **kwargs: Any
    ) -> dict[str, Any]: ...

    async def get_user_info(self, access_token: str) -> UserData: ...

    async def refresh_access_token(
        self, refresh_token: str
    ) -> dict[str, Any] | None: ...


class CredentialsProvider(AuthProvider, Protocol):
    auth_type: str

    async def authenticate(self, credentials: dict[str, Any]) -> UserData | None: ...


class SessionStrategy(Protocol):
    async def create(self, user: UserData, **kwargs: Any) -> str: ...

    async def validate(self, token: str) -> UserData | None: ...

    async def invalidate(self, token: str) -> None: ...

    async def refresh(self, token: str) -> str | None: ...


class SessionBackend(Protocol):
    async def read(self, session_id: str) -> dict[str, Any] | None: ...

    async def write(self, session_id: str, data: dict[str, Any], ttl: int) -> None: ...

    async def delete(self, session_id: str) -> None: ...

    async def exists(self, session_id: str) -> bool: ...


class EmailTransport(Protocol):
    async def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> None: ...


class EventHooks:
    async def on_signup(self, user: UserData) -> None:
        pass

    async def on_signin(self, user: UserData, provider: str) -> None:
        pass

    async def on_signout(self, user: UserData) -> None:
        pass

    async def on_token_refresh(self, user: UserData) -> None:
        pass

    async def on_email_verify(self, user: UserData) -> None:
        pass

    async def on_password_reset(self, user: UserData) -> None:
        pass

    async def on_oauth_link(self, user: UserData, provider: str) -> None:
        pass

    async def allow_signin(self, user: UserData, provider: str) -> bool:
        return True

    async def modify_session(
        self, session: dict[str, Any], user: UserData
    ) -> dict[str, Any]:
        return session

    async def modify_jwt(self, token: dict[str, Any], user: UserData) -> dict[str, Any]:
        return token

from __future__ import annotations

from typing import Any, Literal, Protocol

from fastauth.types import OAuthAccountData, RoleData, SessionData, TokenData, UserData


class UserAdapter(Protocol):
    """Protocol for reading and writing user records.

    Implement this interface to integrate FastAuth with any data store.
    The :class:`~fastauth.adapters.sqlalchemy.SQLAlchemyAdapter` provides a
    ready-made implementation; for testing use
    :class:`~fastauth.adapters.memory.MemoryUserAdapter`.
    """

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
    """
    Protocol for persisting server-side sessions (``session_strategy="database"``).
    """

    async def create_session(self, session: SessionData) -> SessionData: ...

    async def get_session(self, session_id: str) -> SessionData | None: ...

    async def delete_session(self, session_id: str) -> None: ...

    async def delete_user_sessions(self, user_id: str) -> None: ...

    async def cleanup_expired(self) -> int: ...


class TokenAdapter(Protocol):
    """Protocol for persisting one-time tokens (email verification, password reset)."""

    async def create_token(self, token: TokenData) -> TokenData: ...

    async def get_token(self, token: str, token_type: str) -> TokenData | None: ...

    async def delete_token(self, token: str) -> None: ...

    async def delete_user_tokens(
        self, user_id: str, token_type: str | None = None
    ) -> None: ...


class OAuthAccountAdapter(Protocol):
    """Protocol for persisting linked OAuth provider accounts."""

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
    """Protocol for managing roles and permissions (RBAC)."""

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
    """Protocol for key-value session storage (OAuth state, server sessions)."""

    async def read(self, session_id: str) -> dict[str, Any] | None: ...

    async def write(self, session_id: str, data: dict[str, Any], ttl: int) -> None: ...

    async def delete(self, session_id: str) -> None: ...

    async def exists(self, session_id: str) -> bool: ...


class EmailTransport(Protocol):
    """Protocol for sending transactional emails."""

    async def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> None: ...


class EventHooks:
    """Base class for FastAuth lifecycle hooks.

    Subclass and override whichever events you care about, then pass an instance
    as ``FastAuthConfig.hooks``.

    Example:
        ```python
        from fastauth.core.protocols import EventHooks
        from fastauth.types import UserData

        class MyHooks(EventHooks):
            async def on_signup(self, user: UserData) -> None:
                await send_welcome_email(user["email"])

            async def modify_jwt(self, token: dict, user: UserData) -> dict:
                token["plan"] = await get_user_plan(user["id"])
                return token

        config = FastAuthConfig(..., hooks=MyHooks())
        ```
    """

    async def on_signup(self, user: UserData) -> None:
        """Called after a new user is created.

        Args:
            user: The newly created user record.
        """
        pass

    async def on_signin(self, user: UserData, provider: str) -> None:
        """Called after a successful sign-in.

        Args:
            user: The authenticated user.
            provider: Provider ID (e.g. ``"credentials"``, ``"google"``).
        """
        pass

    async def on_signout(self, user: UserData) -> None:
        """Called after a user signs out.

        Args:
            user: The user who signed out.
        """
        pass

    async def on_token_refresh(self, user: UserData) -> None:
        """Called after a token pair is refreshed.

        Args:
            user: The user whose tokens were refreshed.
        """
        pass

    async def on_email_verify(self, user: UserData) -> None:
        """Called after a user successfully verifies their email address.

        Args:
            user: The user whose email was verified.
        """
        pass

    async def on_password_reset(self, user: UserData) -> None:
        """Called after a user successfully resets their password.

        Args:
            user: The user who reset their password.
        """
        pass

    async def on_oauth_link(self, user: UserData, provider: str) -> None:
        """Called after an OAuth account is linked to an existing user.

        Args:
            user: The user who linked the account.
            provider: The OAuth provider ID (e.g. ``"google"``).
        """
        pass

    async def allow_signin(self, user: UserData, provider: str) -> bool:
        """Gate hook — return ``False`` to block sign-in for a specific user.

        Runs before the session or token is issued. Returning ``False`` causes
        FastAuth to respond with HTTP 403.

        Args:
            user: The user attempting to sign in.
            provider: The provider being used.

        Returns:
            ``True`` to allow sign-in, ``False`` to deny it.
        """
        return True

    async def modify_session(
        self, session: dict[str, Any], user: UserData
    ) -> dict[str, Any]:
        """Mutate the database session payload before it is persisted.

        Only called when ``session_strategy="database"``.

        Args:
            session: The default session dict.
            user: The authenticated user.

        Returns:
            The (possibly modified) session dict.
        """
        return session

    async def modify_jwt(self, token: dict[str, Any], user: UserData) -> dict[str, Any]:
        """Mutate the JWT payload before it is signed.

        Use this to embed extra claims such as roles, permissions, or subscription
        tiers directly in the token so downstream services don't need a database
        lookup.

        Args:
            token: The default token payload (includes ``sub``, ``type``, ``exp``).
            user: The authenticated user.

        Returns:
            The (possibly modified) token payload.
        """
        return token

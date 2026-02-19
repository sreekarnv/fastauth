from __future__ import annotations

from typing import TYPE_CHECKING

from fastauth._compat import require
from fastauth.config import FastAuthConfig

if TYPE_CHECKING:
    from fastauth.core.emails import EmailDispatcher
    from fastauth.core.jwks import JWKSManager
    from fastauth.core.protocols import RoleAdapter, SessionAdapter


class FastAuth:
    """
    Central FastAuth instance wires configuration, providers, and adapters together.

    Pass a :class:`~fastauth.config.FastAuthConfig` to the constructor, then call
    :meth:`mount` to attach all authentication routes to a FastAPI application.

    Example:
        ```python
        from fastauth import FastAuth, FastAuthConfig
        from fastauth.providers.credentials import CredentialsProvider
        from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter

        adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

        config = FastAuthConfig(
            secret="change-me-in-production",
            providers=[CredentialsProvider()],
            adapter=adapter.user,
            token_adapter=adapter.token,
        )

        auth = FastAuth(config)
        ```
    """

    def __init__(self, config: FastAuthConfig) -> None:
        """Initialize FastAuth with the given configuration.

        Args:
            config: A fully-populated :class:`~fastauth.config.FastAuthConfig`.
        """
        self.config = config
        self.session_adapter: SessionAdapter | None = None
        self.role_adapter: RoleAdapter | None = None
        self.jwks_manager: JWKSManager | None = None
        self.email_dispatcher: EmailDispatcher | None = None

        if config.email_transport:
            from fastauth.core.emails import EmailDispatcher

            self.email_dispatcher = EmailDispatcher(
                transport=config.email_transport,
                base_url=config.base_url,
            )

    def mount(self, app: object) -> None:
        """Mount all FastAuth routes onto a FastAPI application.

        Attaches the authentication router at ``config.route_prefix`` (default
        ``/auth``). Also mounts the ``/.well-known/jwks.json`` endpoint when a
        JWKS manager has been initialized.

        Args:
            app: A :class:`fastapi.FastAPI` instance.

        Raises:
            AssertionError: If *app* is not a :class:`fastapi.FastAPI` instance.
            MissingDependencyError: If the ``fastapi`` extra is not installed.
        """
        require("fastapi", "fastapi")

        from fastapi import FastAPI

        from fastauth.api.router import create_router

        assert isinstance(app, FastAPI)
        app.state.fastauth = self
        router = create_router(self)
        app.include_router(router, prefix=self.config.route_prefix)

        # Mount JWKS endpoint at root (not under route_prefix)
        if self.jwks_manager:
            from fastauth.api.jwks import create_jwks_router

            jwks_router = create_jwks_router(self)
            app.include_router(jwks_router)

    async def initialize_jwks(self) -> None:
        """Initialize the JWKS manager for RSA-based JWT signing.

        Must be called inside the application lifespan startup handler when using
        ``RS256`` / ``RS512`` algorithms with ``jwks_enabled=True``.

        Example:
            ```python
            from contextlib import asynccontextmanager
            from fastapi import FastAPI

            @asynccontextmanager
            async def lifespan(app: FastAPI):
                await auth.initialize_jwks()
                yield

            app = FastAPI(lifespan=lifespan)
            auth.mount(app)
            ```
        """
        if self.config.jwt.algorithm.startswith("RS"):
            from fastauth.core.jwks import JWKSManager

            self.jwks_manager = JWKSManager(self.config.jwt)
            await self.jwks_manager.initialize()

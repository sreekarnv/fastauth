from __future__ import annotations

from typing import TYPE_CHECKING

from fastauth._compat import require
from fastauth.config import FastAuthConfig

if TYPE_CHECKING:
    from fastauth.core.jwks import JWKSManager
    from fastauth.core.protocols import RoleAdapter, SessionAdapter


class FastAuth:
    def __init__(self, config: FastAuthConfig) -> None:
        self.config = config
        self.session_adapter: SessionAdapter | None = None
        self.role_adapter: RoleAdapter | None = None
        self.jwks_manager: JWKSManager | None = None

    def mount(self, app: object) -> None:
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
        if self.config.jwt.algorithm.startswith("RS"):
            from fastauth.core.jwks import JWKSManager

            self.jwks_manager = JWKSManager(self.config.jwt)
            await self.jwks_manager.initialize()

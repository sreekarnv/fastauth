from __future__ import annotations

from fastauth._compat import require
from fastauth.config import FastAuthConfig


class FastAuth:
    def __init__(self, config: FastAuthConfig) -> None:
        self.config = config

    def mount(self, app: object) -> None:
        require("fastapi", "fastapi")

        from fastapi import FastAPI

        from fastauth.api.router import create_router

        assert isinstance(app, FastAPI)
        app.state.fastauth = self
        router = create_router(self)
        app.include_router(router, prefix=self.config.route_prefix)

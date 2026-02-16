from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse


def create_jwks_router(auth: object) -> APIRouter:
    router = APIRouter()

    @router.get("/.well-known/jwks.json")
    async def jwks_endpoint(request: Request) -> JSONResponse:
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth
        if not fa.jwks_manager:
            return JSONResponse({"keys": []})
        return JSONResponse(fa.jwks_manager.get_jwks())

    return router

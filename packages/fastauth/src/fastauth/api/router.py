from __future__ import annotations

from fastapi import APIRouter

from fastauth.api.auth import create_auth_router


def create_router(auth: object) -> APIRouter:
    router = APIRouter()
    router.include_router(create_auth_router(auth), tags=["auth"])
    return router

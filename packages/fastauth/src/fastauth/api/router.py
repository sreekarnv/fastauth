from __future__ import annotations

from fastapi import APIRouter

from fastauth.api.auth import create_auth_router
from fastauth.api.rbac import create_rbac_router
from fastauth.api.session import create_session_router


def create_router(auth: object) -> APIRouter:
    router = APIRouter()
    router.include_router(create_auth_router(auth), tags=["auth"])
    router.include_router(create_session_router(auth), tags=["sessions"])
    router.include_router(create_rbac_router(auth), tags=["rbac"])
    return router

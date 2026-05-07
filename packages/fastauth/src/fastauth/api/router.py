from fastapi import APIRouter

from fastauth.api.account import create_account_router
from fastauth.api.auth import create_auth_router
from fastauth.api.oauth import create_oauth_router
from fastauth.api.rbac import create_rbac_router
from fastauth.api.session import create_session_router
from fastauth.api.token import create_token_router


def create_router(auth: object) -> APIRouter:
    from fastauth.app import FastAuth
    from fastauth.providers.magic_links import MagicLinksProvider

    assert isinstance(auth, FastAuth)

    router = APIRouter()
    router.include_router(create_auth_router(auth), tags=["auth"])
    router.include_router(create_token_router(auth), tags=["token"])
    router.include_router(create_session_router(auth), tags=["sessions"])
    router.include_router(create_rbac_router(auth), tags=["rbac"])
    router.include_router(create_oauth_router(auth), tags=["oauth"])
    router.include_router(create_account_router(auth), tags=["account"])

    if any(isinstance(p, MagicLinksProvider) for p in auth.config.providers):
        from fastauth.api.magic_links import create_magic_links_router

        router.include_router(create_magic_links_router(auth), tags=["magic_links"])

    if auth.config.passkey_adapter and auth.config.passkey_state_store:
        from fastauth.api.passkeys import create_passkeys_router

        router.include_router(create_passkeys_router(auth), tags=["passkeys"])

    return router

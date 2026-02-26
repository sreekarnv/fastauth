from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from fastauth.api.auth import MessageResponse, _set_auth_cookies
from fastauth.app import FastAuth
from fastauth.core.tokens import create_token_pair
from fastauth.exceptions import AuthenticationError
from fastauth.providers.magic_links import MagicLinksProvider


class MagicLinkRequest(BaseModel):
    email: EmailStr


def create_magic_links_router(auth: object) -> APIRouter:
    assert isinstance(auth, FastAuth)

    fa: FastAuth = auth
    router = APIRouter(prefix="/magic-links")

    def _get_provider() -> MagicLinksProvider:
        for provider in fa.config.providers:
            if isinstance(provider, MagicLinksProvider):
                return provider
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="MagicLinksProvider is not configured",
        )

    @router.post("/login")
    async def magic_link_login(input: MagicLinkRequest) -> MessageResponse:
        provider = _get_provider()

        user = await fa.config.adapter.get_user_by_email(input.email)

        if not user:
            user = await fa.config.adapter.create_user(
                email=input.email, hashed_password=None
            )

        await provider.send_login_request(fa, user)

        return MessageResponse(message="Magic link sent — check your email")

    @router.get("/callback")
    async def magic_link_callback(response: Response, token: str) -> dict:
        provider = _get_provider()

        try:
            user = await provider.authenticate(fa, token)
        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            ) from e

        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive",
            )

        if fa.config.hooks:
            allowed = await fa.config.hooks.allow_signin(user, "magic_link")
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sign-in not allowed",
                )

        tokens = create_token_pair(user, fa.config, fa.jwks_manager)

        if fa.config.token_delivery == "cookie":
            _set_auth_cookies(response, tokens, fa)

        if fa.config.hooks:
            await fa.config.hooks.on_signin(user, "magic_link")

        return dict(tokens)

    return router

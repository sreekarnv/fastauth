from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, EmailStr

from fastauth.api.auth import MessageResponse, _issue_tracked_tokens, _set_auth_cookies
from fastauth.api.schemas import ErrorDetail
from fastauth.app import FastAuth
from fastauth.exceptions import AuthenticationError
from fastauth.providers.magic_links import MagicLinksProvider


class MagicLinkRequest(BaseModel):
    email: EmailStr


def create_magic_links_router(auth: object) -> APIRouter:
    assert isinstance(auth, FastAuth)

    fa: FastAuth = auth
    router = APIRouter(
        prefix="/magic-links",
        responses={
            401: {
                "model": ErrorDetail,
                "description": "Authentication required or token invalid",
            },
            403: {"model": ErrorDetail, "description": "Access forbidden"},
            501: {
                "model": ErrorDetail,
                "description": "MagicLinksProvider not configured",
            },
        },
    )

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
            if fa.role_adapter and fa.config.default_role:
                from fastauth.core.rbac import assign_default_role

                await assign_default_role(
                    fa.role_adapter, user["id"], fa.config.default_role
                )
            if fa.config.hooks:
                await fa.config.hooks.on_signup(user)

        await provider.send_login_request(fa, user)

        if fa.config.hooks:
            await fa.config.hooks.on_magic_link_sent(user)

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

        if not user.get("email_verified"):
            user = await fa.config.adapter.update_user(user["id"], email_verified=True)
            if fa.config.hooks:
                await fa.config.hooks.on_email_verify(user)

        tokens = await _issue_tracked_tokens(fa, user)

        if fa.config.token_delivery == "cookie":
            _set_auth_cookies(response, tokens, fa)

        if fa.config.hooks:
            await fa.config.hooks.on_signin(user, "magic_link")

        return dict(tokens)

    return router

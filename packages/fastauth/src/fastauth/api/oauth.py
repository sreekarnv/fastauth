from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from fastauth.api.auth import _issue_tracked_tokens
from fastauth.api.deps import require_auth
from fastauth.api.schemas import ErrorDetail
from fastauth.core.oauth import (
    complete_oauth_flow,
    initiate_link_flow,
    initiate_oauth_flow,
    link_oauth_account,
)
from fastauth.exceptions import ProviderError

if TYPE_CHECKING:
    from fastauth.types import UserData


class AuthorizeResponse(BaseModel):
    url: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class OAuthAccountResponse(BaseModel):
    provider: str
    provider_account_id: str


class MessageResponse(BaseModel):
    message: str


def _get_oauth_provider(fa: object, provider_id: str):
    from fastauth.app import FastAuth

    assert isinstance(fa, FastAuth)
    for p in fa.config.providers:
        if (
            getattr(p, "id", None) == provider_id
            and getattr(p, "auth_type", None) == "oauth"
        ):
            return p
    return None


def create_oauth_router(auth: object) -> APIRouter:
    router = APIRouter(
        prefix="/oauth",
        responses={
            400: {"model": ErrorDetail, "description": "Bad request or missing configuration"},
            401: {"model": ErrorDetail, "description": "Authentication required or token invalid"},
            403: {"model": ErrorDetail, "description": "Access forbidden"},
            404: {"model": ErrorDetail, "description": "Provider or resource not found"},
        },
    )

    @router.get("/{provider}/authorize", response_model=AuthorizeResponse)
    async def authorize(
        request: Request, provider: str, redirect_uri: str
    ) -> AuthorizeResponse:
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth
        oauth_provider = _get_oauth_provider(fa, provider)
        if not oauth_provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OAuth provider '{provider}' not found",
            )
        if not fa.config.oauth_state_store:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="oauth_state_store is not configured",
            )

        url, _state = await initiate_oauth_flow(
            provider=oauth_provider,
            redirect_uri=redirect_uri,
            state_store=fa.config.oauth_state_store,
        )
        return AuthorizeResponse(url=url)

    @router.get("/{provider}/callback")
    async def callback(
        request: Request,
        provider: str,
        code: str,
        state: str,
    ):
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth
        oauth_provider = _get_oauth_provider(fa, provider)
        if not oauth_provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OAuth provider '{provider}' not found",
            )
        if not fa.config.oauth_state_store:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="oauth_state_store is not configured",
            )
        if not fa.config.oauth_adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="oauth_adapter is not configured",
            )

        callback_uri = str(request.url_for("callback", provider=provider))

        try:
            user, is_new, email_verified_now = await complete_oauth_flow(
                provider=oauth_provider,
                code=code,
                state=state,
                redirect_uri=callback_uri,
                state_store=fa.config.oauth_state_store,
                user_adapter=fa.config.adapter,
                oauth_adapter=fa.config.oauth_adapter,
            )
        except ProviderError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

        if fa.config.hooks:
            if is_new:
                await fa.config.hooks.on_signup(user)
            if email_verified_now and not is_new:
                await fa.config.hooks.on_email_verify(user)
            allowed = await fa.config.hooks.allow_signin(user, provider)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sign-in not allowed",
                )
            await fa.config.hooks.on_signin(user, provider)
            await fa.config.hooks.on_oauth_link(user, provider)

        tokens = await _issue_tracked_tokens(fa, user)

        if fa.config.oauth_redirect_url:
            params = urlencode(
                {
                    "access_token": tokens["access_token"],
                    "refresh_token": tokens["refresh_token"],
                    "token_type": tokens["token_type"],
                    "expires_in": tokens["expires_in"],
                }
            )
            return RedirectResponse(
                url=f"{fa.config.oauth_redirect_url}?{params}",
                status_code=status.HTTP_302_FOUND,
            )

        return TokenResponse(**tokens)

    @router.get("/accounts", response_model=list[OAuthAccountResponse])
    async def list_accounts(
        request: Request,
        user: UserData = Depends(require_auth),
    ) -> list[OAuthAccountResponse]:
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth
        if not fa.config.oauth_adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="oauth_adapter is not configured",
            )
        accounts = await fa.config.oauth_adapter.get_user_oauth_accounts(user["id"])
        return [
            OAuthAccountResponse(
                provider=a["provider"],
                provider_account_id=a["provider_account_id"],
            )
            for a in accounts
        ]

    @router.delete("/accounts/{provider}", response_model=MessageResponse)
    async def unlink_account(
        request: Request,
        provider: str,
        user: UserData = Depends(require_auth),
    ) -> MessageResponse:
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth
        if not fa.config.oauth_adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="oauth_adapter is not configured",
            )
        accounts = await fa.config.oauth_adapter.get_user_oauth_accounts(user["id"])
        target = next((a for a in accounts if a["provider"] == provider), None)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No linked {provider} account found",
            )
        await fa.config.oauth_adapter.delete_oauth_account(
            provider=target["provider"],
            provider_account_id=target["provider_account_id"],
        )
        return MessageResponse(message="Account unlinked")

    @router.get(
        "/{provider}/link",
        response_model=AuthorizeResponse,
        responses={409: {"model": ErrorDetail, "description": "Provider already linked to a user"}},
    )
    async def link_begin(
        request: Request,
        provider: str,
        redirect_uri: str,
        user: UserData = Depends(require_auth),
    ) -> AuthorizeResponse:
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth
        oauth_provider = _get_oauth_provider(fa, provider)
        if not oauth_provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OAuth provider '{provider}' not found",
            )
        if not fa.config.oauth_state_store:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="oauth_state_store is not configured",
            )
        if not fa.config.oauth_adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="oauth_adapter is not configured",
            )
        url, _ = await initiate_link_flow(
            provider=oauth_provider,
            redirect_uri=redirect_uri,
            state_store=fa.config.oauth_state_store,
            user_id=user["id"],
        )
        return AuthorizeResponse(url=url)

    @router.get("/{provider}/link/callback", response_model=MessageResponse)
    async def link_callback(
        request: Request,
        provider: str,
        code: str,
        state: str,
    ) -> MessageResponse:
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth
        oauth_provider = _get_oauth_provider(fa, provider)
        if not oauth_provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OAuth provider '{provider}' not found",
            )
        if not fa.config.oauth_state_store:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="oauth_state_store is not configured",
            )
        if not fa.config.oauth_adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="oauth_adapter is not configured",
            )
        redirect_uri = str(request.url_for("link_callback", provider=provider))
        try:
            _, user = await link_oauth_account(
                provider=oauth_provider,
                code=code,
                state=state,
                redirect_uri=redirect_uri,
                state_store=fa.config.oauth_state_store,
                user_adapter=fa.config.adapter,
                oauth_adapter=fa.config.oauth_adapter,
            )
        except ProviderError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
        if fa.config.hooks:
            await fa.config.hooks.on_oauth_link(user, provider)
        return MessageResponse(message=f"{provider.capitalize()} account linked successfully")

    return router

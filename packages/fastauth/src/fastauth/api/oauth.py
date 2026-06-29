from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from fastauth.api.auth import (
    MessageResponse,
    _issue_tracked_tokens,
    _set_auth_cookies,
)
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
    from fastauth.types import TokenPair, UserData


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


def _oauth_signin_response(
    fa: object,
    tokens: "TokenPair",
    response: Response,
):
    """Return the appropriate OAuth sign-in response.

    In ``"cookie"`` mode the tokens are attached to *response* as
    ``HttpOnly`` cookies and the body intentionally contains no token
    material. In ``"json"`` mode the tokens are returned in the body.
    When ``oauth_redirect_url`` is configured the response is a 302 to
    that URL with the tokens as cookies.
    """
    from fastauth.app import FastAuth

    assert isinstance(fa, FastAuth)
    if fa.config.oauth_redirect_url:
        redirect = RedirectResponse(
            url=fa.config.oauth_redirect_url,
            status_code=status.HTTP_302_FOUND,
        )
        _set_auth_cookies(redirect, tokens, fa)
        return redirect
    if fa.config.token_delivery == "cookie":
        _set_auth_cookies(response, tokens, fa)
        return MessageResponse(message="Authentication successful")
    return TokenResponse(**tokens)


def create_oauth_router(auth: object) -> APIRouter:
    router = APIRouter(
        prefix="/oauth",
        responses={
            400: {
                "model": ErrorDetail,
                "description": "Bad request or missing configuration",
            },
            401: {
                "model": ErrorDetail,
                "description": "Authentication required or token invalid",
            },
            403: {"model": ErrorDetail, "description": "Access forbidden"},
            404: {
                "model": ErrorDetail,
                "description": "Provider or resource not found",
            },
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

    @router.get("/{provider}/callback", response_model=None)
    async def callback(
        request: Request,
        response: Response,
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

        try:
            user, is_new, email_verified_now = await complete_oauth_flow(
                provider=oauth_provider,
                code=code,
                state=state,
                redirect_uri=str(request.url_for("callback", provider=provider)),
                state_store=fa.config.oauth_state_store,
                user_adapter=fa.config.adapter,
                oauth_adapter=fa.config.oauth_adapter,
                store_provider_tokens=fa.config.store_oauth_provider_tokens,
            )
        except ProviderError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

        if is_new and fa.role_adapter and fa.config.default_role:
            from fastauth.core.rbac import assign_default_role

            await assign_default_role(
                fa.role_adapter, user["id"], fa.config.default_role
            )

        if fa.config.hooks:
            if is_new:
                await fa.config.hooks.on_signup(user)
            if email_verified_now and not is_new:
                await fa.config.hooks.on_email_verify(user)
            # `allow_signin` is evaluated *before* tokens are issued so a
            # denied sign-in produces no tokens and triggers no
            # `on_token_refresh` / `on_signin` callbacks. `on_oauth_link`
            # intentionally only fires for explicit link flows — see
            # `/auth/oauth/{provider}/link/callback`.
            allowed = await fa.config.hooks.allow_signin(user, provider)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sign-in not allowed",
                )
            await fa.config.hooks.on_signin(user, provider)

        tokens = await _issue_tracked_tokens(fa, user)
        return _oauth_signin_response(fa, tokens, response)

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
        responses={
            409: {
                "model": ErrorDetail,
                "description": "Provider already linked to a user",
            }
        },
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
        try:
            _, user = await link_oauth_account(
                provider=oauth_provider,
                code=code,
                state=state,
                redirect_uri=str(request.url_for("link_callback", provider=provider)),
                state_store=fa.config.oauth_state_store,
                user_adapter=fa.config.adapter,
                oauth_adapter=fa.config.oauth_adapter,
                store_provider_tokens=fa.config.store_oauth_provider_tokens,
            )
        except ProviderError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
        if fa.config.hooks:
            await fa.config.hooks.on_oauth_link(user, provider)
        return MessageResponse(
            message=f"{provider.capitalize()} account linked successfully"
        )

    return router

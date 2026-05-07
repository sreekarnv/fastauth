from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from fastauth.api.deps import require_auth
from fastauth.core.tokens import decode_token

if TYPE_CHECKING:
    from fastauth.types import UserData


class TokenRequest(BaseModel):
    token: str


class IntrospectResponse(BaseModel):
    active: bool
    sub: str | None = None
    exp: int | None = None
    jti: str | None = None
    token_type: str | None = None
    email: str | None = None


class MessageResponse(BaseModel):
    message: str


def create_token_router(auth: object) -> APIRouter:
    router = APIRouter(prefix="/token")

    @router.post("/introspect", response_model=IntrospectResponse)
    async def introspect(
        request: Request,
        body: TokenRequest,
        _user: UserData = Depends(require_auth),
    ) -> IntrospectResponse:
        """Inspect a token's active status (RFC 7662).

        Returns active=true when the token is valid and, for refresh tokens,
        present in the JTI allowlist. Returns active=false for any expired,
        malformed, or revoked token — never raises 4xx for bad tokens.
        """
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth

        try:
            claims = decode_token(body.token, fa.config, fa.jwks_manager)
        except Exception:
            return IntrospectResponse(active=False)

        # For refresh tokens, verify JTI is still in the allowlist
        if claims.get("type") == "refresh" and fa.config.token_adapter:
            jti = claims.get("jti")
            stored = (
                await fa.config.token_adapter.get_token(jti, "refresh_jti")
                if jti
                else None
            )
            if not stored:
                return IntrospectResponse(active=False)

        return IntrospectResponse(
            active=True,
            sub=claims.get("sub"),
            exp=claims.get("exp"),
            jti=claims.get("jti"),
            token_type=claims.get("type"),
            email=claims.get("email"),
        )

    @router.post("/revoke", response_model=MessageResponse)
    async def revoke(
        request: Request,
        body: TokenRequest,
        user: UserData = Depends(require_auth),
    ) -> MessageResponse:
        """Revoke a refresh token (RFC 7009).

        Only the token owner may revoke their own token. Removes the JTI from
        the allowlist so any subsequent refresh attempt is rejected.
        """
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth

        if not fa.config.token_adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token adapter is not configured",
            )

        try:
            claims = decode_token(body.token, fa.config, fa.jwks_manager)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token",
            ) from e

        if claims.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only refresh tokens can be revoked",
            )

        if claims.get("sub") != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot revoke another user's token",
            )

        jti = claims.get("jti")
        if jti:
            await fa.config.token_adapter.delete_token(jti)

        return MessageResponse(message="Token revoked")

    return router

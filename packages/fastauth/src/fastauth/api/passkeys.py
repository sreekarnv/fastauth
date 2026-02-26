from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
)

from fastauth._compat import require
from fastauth.api.auth import _issue_tracked_tokens
from fastauth.api.deps import require_auth

if TYPE_CHECKING:
    from fastauth.app import FastAuth
    from fastauth.core.protocols import PasskeyAdapter, SessionBackend
    from fastauth.providers.passkey import PasskeyProvider
    from fastauth.types import UserData


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _extract_challenge(credential: dict[str, Any]) -> str:
    raw = credential["response"]["clientDataJSON"]
    padded = raw + "=" * (-len(raw) % 4)
    client_data = json.loads(base64.urlsafe_b64decode(padded))
    return client_data["challenge"]


def create_passkeys_router(auth: object) -> APIRouter:
    require("webauthn", "webauthn")

    from fastauth.app import FastAuth
    from fastauth.providers.passkey import PasskeyProvider

    assert isinstance(auth, FastAuth)
    assert auth.config.passkey_adapter is not None
    assert auth.config.passkey_state_store is not None

    passkey_adapter: PasskeyAdapter = auth.config.passkey_adapter
    state_store: SessionBackend = auth.config.passkey_state_store
    fa: FastAuth = auth

    router = APIRouter(prefix="/passkeys")

    def _get_provider() -> PasskeyProvider:
        for provider in fa.config.providers:
            if isinstance(provider, PasskeyProvider):
                return provider
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PasskeyProvider is not configured",
        )

    @router.post("/register/begin")
    async def begin_registration(
        user: UserData = Depends(require_auth),
    ) -> Response:
        provider = _get_provider()

        existing = await passkey_adapter.get_passkeys_by_user(user["id"])
        exclude = [
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(p["id"]))
            for p in existing
        ]

        options = generate_registration_options(
            rp_id=provider.rp_id,
            rp_name=provider.rp_name,
            user_id=user["id"].encode(),
            user_name=user["email"],
            user_display_name=user.get("name") or user["email"],
            exclude_credentials=exclude,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
            ),
        )

        challenge_b64 = _b64url_encode(options.challenge)
        await state_store.write(
            f"pk_reg:{challenge_b64}",
            {"user_id": user["id"], "challenge": challenge_b64},
            300,
        )

        return Response(content=options_to_json(options), media_type="application/json")

    @router.post("/register/complete", status_code=status.HTTP_201_CREATED)
    async def complete_registration(
        request: Request,
        user: UserData = Depends(require_auth),
    ) -> dict[str, Any]:
        provider = _get_provider()

        body = await request.json()
        credential = body.get("credential", body)
        name: str = body.get("name", "Passkey") if "credential" in body else "Passkey"

        challenge_b64 = _extract_challenge(credential)
        stored = await state_store.read(f"pk_reg:{challenge_b64}")

        if not stored or stored["user_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired challenge",
            )

        try:
            verified = verify_registration_response(
                credential=credential,
                expected_challenge=base64url_to_bytes(challenge_b64),
                expected_rp_id=provider.rp_id,
                expected_origin=provider.origins,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration verification failed: {exc}",
            ) from exc

        await state_store.delete(f"pk_reg:{challenge_b64}")

        credential_id = _b64url_encode(verified.credential_id)
        aaguid = str(getattr(verified, "aaguid", "") or "")

        passkey = await passkey_adapter.create_passkey(
            user_id=user["id"],
            credential_id=credential_id,
            public_key=verified.credential_public_key,
            sign_count=verified.sign_count,
            aaguid=aaguid,
            name=name,
        )

        if fa.config.hooks:
            await fa.config.hooks.on_passkey_registered(user, passkey)

        return {
            "id": passkey["id"],
            "name": passkey["name"],
            "created_at": passkey["created_at"],
        }

    @router.get("")
    async def list_passkeys(
        user: UserData = Depends(require_auth),
    ) -> list[dict[str, Any]]:
        passkeys = await passkey_adapter.get_passkeys_by_user(user["id"])
        return [
            {
                "id": p["id"],
                "name": p["name"],
                "aaguid": p["aaguid"],
                "created_at": p["created_at"],
                "last_used_at": p["last_used_at"],
            }
            for p in passkeys
        ]

    @router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_passkey(
        credential_id: str,
        user: UserData = Depends(require_auth),
    ) -> None:
        passkey = await passkey_adapter.get_passkey(credential_id)
        if not passkey or passkey["user_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Passkey not found",
            )

        await passkey_adapter.delete_passkey(credential_id)

        if fa.config.hooks:
            await fa.config.hooks.on_passkey_deleted(user, passkey)

    @router.post("/authenticate/begin")
    async def begin_authentication(
        request: Request,
    ) -> Response:
        provider = _get_provider()

        email: str | None = None
        try:
            body = await request.json()
            email = body.get("email")
        except Exception:
            pass

        allow_credentials: list[PublicKeyCredentialDescriptor] = []
        user_id: str | None = None

        if email:
            lookup = await fa.config.adapter.get_user_by_email(email)
            if lookup:
                user_id = lookup["id"]
                user_passkeys = await passkey_adapter.get_passkeys_by_user(lookup["id"])
                allow_credentials = [
                    PublicKeyCredentialDescriptor(id=base64url_to_bytes(p["id"]))
                    for p in user_passkeys
                ]

        options = generate_authentication_options(
            rp_id=provider.rp_id,
            allow_credentials=allow_credentials,
        )

        challenge_b64 = _b64url_encode(options.challenge)
        await state_store.write(
            f"pk_auth:{challenge_b64}",
            {"user_id": user_id, "challenge": challenge_b64},
            300,
        )

        return Response(content=options_to_json(options), media_type="application/json")

    @router.post("/authenticate/complete")
    async def complete_authentication(
        request: Request,
        response: Response,
    ) -> dict[str, Any]:
        from fastauth.api.auth import _set_auth_cookies

        provider = _get_provider()

        body = await request.json()
        credential = body.get("credential", body)

        challenge_b64 = _extract_challenge(credential)
        stored = await state_store.read(f"pk_auth:{challenge_b64}")

        if not stored:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired challenge",
            )

        credential_id: str = credential.get("id") or credential.get("rawId", "")
        passkey = await passkey_adapter.get_passkey(credential_id)

        if not passkey:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Passkey not found",
            )

        try:
            verified = verify_authentication_response(
                credential=credential,
                expected_challenge=base64url_to_bytes(challenge_b64),
                expected_rp_id=provider.rp_id,
                expected_origin=provider.origins,
                credential_public_key=passkey["public_key"],
                credential_current_sign_count=passkey["sign_count"],
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication verification failed: {exc}",
            ) from exc

        await state_store.delete(f"pk_auth:{challenge_b64}")

        now = datetime.now(timezone.utc).isoformat()
        await passkey_adapter.update_sign_count(
            credential_id=credential_id,
            sign_count=verified.new_sign_count,
            last_used_at=now,
        )

        user = await fa.config.adapter.get_user_by_id(passkey["user_id"])

        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        if fa.config.hooks:
            allowed = await fa.config.hooks.allow_signin(user, "passkey")
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sign-in not allowed",
                )

        tokens = await _issue_tracked_tokens(fa, user)

        if fa.config.token_delivery == "cookie":
            _set_auth_cookies(response, tokens, fa)

        if fa.config.hooks:
            await fa.config.hooks.on_signin(user, "passkey")

        return dict(tokens)

    return router

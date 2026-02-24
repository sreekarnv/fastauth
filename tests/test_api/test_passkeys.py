import base64
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import MemoryPasskeyAdapter, MemoryUserAdapter
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.core.protocols import EventHooks
from fastauth.providers.credentials import CredentialsProvider
from fastauth.providers.passkey import PasskeyProvider
from fastauth.session_backends.memory import MemorySessionBackend
from fastauth.types import PasskeyData, UserData
from httpx import ASGITransport, AsyncClient

RP_ID = "testserver"
ORIGIN = "http://testserver"


def _build_app(
    user_adapter=None,
    passkey_adapter=None,
    state_store=None,
    hooks=None,
):
    user_adapter = user_adapter or MemoryUserAdapter()
    passkey_adapter = passkey_adapter or MemoryPasskeyAdapter()
    state_store = state_store or MemorySessionBackend()

    config = FastAuthConfig(
        secret="test-secret-passkeys",
        providers=[
            CredentialsProvider(),
            PasskeyProvider(rp_id=RP_ID, rp_name="Test App", origin=ORIGIN),
        ],
        adapter=user_adapter,
        passkey_adapter=passkey_adapter,
        passkey_state_store=state_store,
        jwt=JWTConfig(algorithm="HS256"),
        hooks=hooks,
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    return app, user_adapter, passkey_adapter, state_store


def _make_client_data_json(challenge_b64: str, typ: str = "webauthn.create") -> str:
    data = {"type": typ, "challenge": challenge_b64, "origin": ORIGIN}
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


def _fake_verified_registration():
    m = MagicMock()
    m.credential_id = b"fake_cred_id_bytes"
    m.credential_public_key = b"fake_pubkey_bytes"
    m.sign_count = 0
    m.aaguid = "00000000-0000-0000-0000-000000000000"
    return m


def _fake_verified_authentication(new_sign_count: int = 1):
    m = MagicMock()
    m.new_sign_count = new_sign_count
    return m


@pytest.fixture
async def passkey_client():
    user_adapter = MemoryUserAdapter()
    passkey_adapter = MemoryPasskeyAdapter()
    state_store = MemorySessionBackend()
    app, *_ = _build_app(user_adapter, passkey_adapter, state_store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c, user_adapter, passkey_adapter, state_store


async def _register_and_login(client, email="pk@example.com", password="Pass123#"):
    resp = await client.post(
        "/auth/register", json={"email": email, "password": password}
    )
    return resp.json()["access_token"]


async def test_begin_registration_returns_options(passkey_client):
    client, *_ = passkey_client
    token = await _register_and_login(client)

    resp = await client.post(
        "/auth/passkeys/register/begin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "challenge" in data
    assert "rp" in data
    assert data["rp"]["id"] == RP_ID


async def test_begin_registration_requires_auth(passkey_client):
    client, *_ = passkey_client
    resp = await client.post("/auth/passkeys/register/begin")
    assert resp.status_code == 401


async def test_begin_registration_excludes_existing_credentials(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client
    token = await _register_and_login(client, "excl@example.com")
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    user_id = me.json()["id"]

    await passkey_adapter.create_passkey(user_id, "exist-cc", b"pk", 0, "", "Existing")

    resp = await client.post(
        "/auth/passkeys/register/begin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "excludeCredentials" in data
    assert len(data["excludeCredentials"]) == 1


async def test_complete_registration_success(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client
    token = await _register_and_login(client, "complete@example.com")

    begin = await client.post(
        "/auth/passkeys/register/begin",
        headers={"Authorization": f"Bearer {token}"},
    )
    challenge_b64 = begin.json()["challenge"]
    client_data_json = _make_client_data_json(challenge_b64, "webauthn.create")

    credential = {
        "id": "ZmFrZV9jcmVkX2lk",
        "rawId": "ZmFrZV9jcmVkX2lk",
        "type": "public-key",
        "response": {
            "clientDataJSON": client_data_json,
            "attestationObject": "fake",
        },
    }

    with patch(
        "fastauth.api.passkeys.verify_registration_response",
        return_value=_fake_verified_registration(),
    ):
        resp = await client.post(
            "/auth/passkeys/register/complete",
            json={"credential": credential, "name": "My Passkey"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["name"] == "My Passkey"
    assert "created_at" in data


async def test_complete_registration_default_name(passkey_client):
    client, *_ = passkey_client
    token = await _register_and_login(client, "defaultname@example.com")

    begin = await client.post(
        "/auth/passkeys/register/begin",
        headers={"Authorization": f"Bearer {token}"},
    )
    challenge_b64 = begin.json()["challenge"]
    client_data_json = _make_client_data_json(challenge_b64, "webauthn.create")

    credential = {
        "id": "ZmFrZV9jcmVkX2lk",
        "rawId": "ZmFrZV9jcmVkX2lk",
        "type": "public-key",
        "response": {"clientDataJSON": client_data_json, "attestationObject": "fake"},
    }

    with patch(
        "fastauth.api.passkeys.verify_registration_response",
        return_value=_fake_verified_registration(),
    ):
        resp = await client.post(
            "/auth/passkeys/register/complete",
            json=credential,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 201
    assert resp.json()["name"] == "Passkey"


async def test_complete_registration_invalid_challenge(passkey_client):
    client, *_ = passkey_client
    token = await _register_and_login(client, "invchall@example.com")

    client_data_json = _make_client_data_json(
        "nonexistent-challenge", "webauthn.create"
    )
    credential = {
        "id": "cred",
        "rawId": "cred",
        "type": "public-key",
        "response": {"clientDataJSON": client_data_json, "attestationObject": "fake"},
    }

    resp = await client.post(
        "/auth/passkeys/register/complete",
        json={"credential": credential},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


async def test_complete_registration_verification_fails(passkey_client):
    client, *_ = passkey_client
    token = await _register_and_login(client, "verifail@example.com")

    begin = await client.post(
        "/auth/passkeys/register/begin",
        headers={"Authorization": f"Bearer {token}"},
    )
    challenge_b64 = begin.json()["challenge"]
    client_data_json = _make_client_data_json(challenge_b64, "webauthn.create")

    credential = {
        "id": "cred",
        "rawId": "cred",
        "type": "public-key",
        "response": {"clientDataJSON": client_data_json, "attestationObject": "fake"},
    }

    with patch(
        "fastauth.api.passkeys.verify_registration_response",
        side_effect=ValueError("invalid signature"),
    ):
        resp = await client.post(
            "/auth/passkeys/register/complete",
            json={"credential": credential},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 400
    assert "verification failed" in resp.json()["detail"]


async def test_complete_registration_fires_hook(passkey_client):
    client, *_ = passkey_client

    class RecordingHooks(EventHooks):
        def __init__(self):
            self.recorded = []

        async def on_passkey_registered(self, user: UserData, passkey: PasskeyData):
            self.recorded.append((user["email"], passkey["name"]))

    hooks = RecordingHooks()
    app, user_adapter, passkey_adapter, state_store = _build_app(hooks=hooks)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        token = await _register_and_login(c, "hooktest@example.com")
        begin = await c.post(
            "/auth/passkeys/register/begin",
            headers={"Authorization": f"Bearer {token}"},
        )
        challenge_b64 = begin.json()["challenge"]
        client_data_json = _make_client_data_json(challenge_b64, "webauthn.create")
        credential = {
            "id": "ZmFrZQ",
            "rawId": "ZmFrZQ",
            "type": "public-key",
            "response": {
                "clientDataJSON": client_data_json,
                "attestationObject": "fake",
            },
        }
        with patch(
            "fastauth.api.passkeys.verify_registration_response",
            return_value=_fake_verified_registration(),
        ):
            await c.post(
                "/auth/passkeys/register/complete",
                json={"credential": credential, "name": "Hooked"},
                headers={"Authorization": f"Bearer {token}"},
            )

    assert len(hooks.recorded) == 1
    assert hooks.recorded[0][0] == "hooktest@example.com"
    assert hooks.recorded[0][1] == "Hooked"


async def test_list_passkeys(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client
    token = await _register_and_login(client, "list@example.com")
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    user_id = me.json()["id"]

    await passkey_adapter.create_passkey(user_id, "cred-a", b"pk", 0, "", "Key A")
    await passkey_adapter.create_passkey(user_id, "cred-b", b"pk", 0, "", "Key B")

    resp = await client.get(
        "/auth/passkeys",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = {p["name"] for p in data}
    assert names == {"Key A", "Key B"}


async def test_list_passkeys_empty(passkey_client):
    client, *_ = passkey_client
    token = await _register_and_login(client, "listempty@example.com")

    resp = await client.get(
        "/auth/passkeys",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_passkeys_only_own(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client
    other = await user_adapter.create_user("other@example.com")
    await passkey_adapter.create_passkey(
        other["id"], "other-cred", b"pk", 0, "", "Other"
    )

    token = await _register_and_login(client, "mine@example.com")
    resp = await client.get(
        "/auth/passkeys",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.json() == []


async def test_delete_passkey_success(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client
    token = await _register_and_login(client, "del@example.com")
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    user_id = me.json()["id"]

    await passkey_adapter.create_passkey(user_id, "del-cred", b"pk", 0, "", "Delete Me")

    resp = await client.delete(
        "/auth/passkeys/del-cred",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204
    assert await passkey_adapter.get_passkey("del-cred") is None


async def test_delete_passkey_not_found(passkey_client):
    client, *_ = passkey_client
    token = await _register_and_login(client, "del404@example.com")

    resp = await client.delete(
        "/auth/passkeys/nonexistent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_delete_passkey_wrong_user(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client
    other = await user_adapter.create_user("otherown@example.com")
    await passkey_adapter.create_passkey(
        other["id"], "other-cred", b"pk", 0, "", "Other"
    )

    token = await _register_and_login(client, "thief@example.com")
    resp = await client.delete(
        "/auth/passkeys/other-cred",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_delete_passkey_fires_hook(passkey_client):
    client, user_adapter, passkey_adapter, state_store = passkey_client

    class RecordingHooks(EventHooks):
        def __init__(self):
            self.deleted = []

        async def on_passkey_deleted(self, user: UserData, passkey: PasskeyData):
            self.deleted.append(passkey["name"])

    hooks = RecordingHooks()
    app, user_adapter2, passkey_adapter2, _ = _build_app(hooks=hooks)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        token = await _register_and_login(c, "delhook@example.com")
        me = await c.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        user_id = me.json()["id"]
        await passkey_adapter2.create_passkey(
            user_id, "hook-cred", b"pk", 0, "", "Hook Key"
        )
        resp = await c.delete(
            "/auth/passkeys/hook-cred",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

    assert hooks.deleted == ["Hook Key"]


async def test_begin_authentication_no_email(passkey_client):
    client, *_ = passkey_client
    resp = await client.post("/auth/passkeys/authenticate/begin", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert "challenge" in data


async def test_begin_authentication_empty_body(passkey_client):
    client, *_ = passkey_client
    resp = await client.post(
        "/auth/passkeys/authenticate/begin",
        content=b"",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200


async def test_begin_authentication_with_email(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client
    user = await user_adapter.create_user("authpk@example.com")
    await passkey_adapter.create_passkey(user["id"], "auth-cc", b"pk", 0, "", "Key")

    resp = await client.post(
        "/auth/passkeys/authenticate/begin",
        json={"email": "authpk@example.com"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "challenge" in data
    assert "allowCredentials" in data
    assert len(data["allowCredentials"]) == 1


async def test_begin_authentication_unknown_email(passkey_client):
    client, *_ = passkey_client
    resp = await client.post(
        "/auth/passkeys/authenticate/begin",
        json={"email": "nobody@example.com"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("allowCredentials", []) == []


async def test_complete_authentication_success(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client
    user = await user_adapter.create_user("authcomp@example.com")
    cred_id = "auth-cred-complete"
    await passkey_adapter.create_passkey(
        user["id"], cred_id, b"stored_pk", 0, "", "Auth Key"
    )

    begin = await client.post(
        "/auth/passkeys/authenticate/begin",
        json={"email": "authcomp@example.com"},
    )
    challenge_b64 = begin.json()["challenge"]
    client_data_json = _make_client_data_json(challenge_b64, "webauthn.get")

    credential = {
        "id": cred_id,
        "rawId": cred_id,
        "type": "public-key",
        "response": {
            "clientDataJSON": client_data_json,
            "authenticatorData": "fake",
            "signature": "fake",
        },
    }

    with patch(
        "fastauth.api.passkeys.verify_authentication_response",
        return_value=_fake_verified_authentication(new_sign_count=1),
    ):
        resp = await client.post(
            "/auth/passkeys/authenticate/complete",
            json={"credential": credential},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_complete_authentication_updates_sign_count(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client
    user = await user_adapter.create_user("signcount@example.com")
    cred_id = "sc-cred"
    await passkey_adapter.create_passkey(user["id"], cred_id, b"pk", 0, "", "SC Key")

    begin = await client.post(
        "/auth/passkeys/authenticate/begin",
        json={"email": "signcount@example.com"},
    )
    challenge_b64 = begin.json()["challenge"]
    client_data_json = _make_client_data_json(challenge_b64, "webauthn.get")

    credential = {
        "id": cred_id,
        "rawId": cred_id,
        "type": "public-key",
        "response": {
            "clientDataJSON": client_data_json,
            "authenticatorData": "fake",
            "signature": "fake",
        },
    }

    with patch(
        "fastauth.api.passkeys.verify_authentication_response",
        return_value=_fake_verified_authentication(new_sign_count=7),
    ):
        await client.post(
            "/auth/passkeys/authenticate/complete",
            json={"credential": credential},
        )

    pk = await passkey_adapter.get_passkey(cred_id)
    assert pk["sign_count"] == 7
    assert pk["last_used_at"] is not None


async def test_complete_authentication_invalid_challenge(passkey_client):
    client, *_ = passkey_client
    client_data_json = _make_client_data_json("invalid-challenge", "webauthn.get")
    credential = {
        "id": "cred",
        "rawId": "cred",
        "type": "public-key",
        "response": {
            "clientDataJSON": client_data_json,
            "authenticatorData": "fake",
            "signature": "fake",
        },
    }
    resp = await client.post(
        "/auth/passkeys/authenticate/complete",
        json={"credential": credential},
    )
    assert resp.status_code == 400


async def test_complete_authentication_passkey_not_found(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client
    await user_adapter.create_user("pknf@example.com")

    begin = await client.post(
        "/auth/passkeys/authenticate/begin",
        json={"email": "pknf@example.com"},
    )
    challenge_b64 = begin.json()["challenge"]
    client_data_json = _make_client_data_json(challenge_b64, "webauthn.get")

    credential = {
        "id": "nonexistent-cred",
        "rawId": "nonexistent-cred",
        "type": "public-key",
        "response": {
            "clientDataJSON": client_data_json,
            "authenticatorData": "fake",
            "signature": "fake",
        },
    }
    resp = await client.post(
        "/auth/passkeys/authenticate/complete",
        json={"credential": credential},
    )
    assert resp.status_code == 401


async def test_complete_authentication_verification_fails(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client
    user = await user_adapter.create_user("verifail2@example.com")
    cred_id = "vf-cred"
    await passkey_adapter.create_passkey(user["id"], cred_id, b"pk", 0, "", "Key")

    begin = await client.post(
        "/auth/passkeys/authenticate/begin",
        json={"email": "verifail2@example.com"},
    )
    challenge_b64 = begin.json()["challenge"]
    client_data_json = _make_client_data_json(challenge_b64, "webauthn.get")

    credential = {
        "id": cred_id,
        "rawId": cred_id,
        "type": "public-key",
        "response": {
            "clientDataJSON": client_data_json,
            "authenticatorData": "fake",
            "signature": "fake",
        },
    }

    with patch(
        "fastauth.api.passkeys.verify_authentication_response",
        side_effect=ValueError("bad signature"),
    ):
        resp = await client.post(
            "/auth/passkeys/authenticate/complete",
            json={"credential": credential},
        )

    assert resp.status_code == 401
    assert "verification failed" in resp.json()["detail"]


async def test_complete_authentication_inactive_user(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client
    user = await user_adapter.create_user("inactive@example.com")
    await user_adapter.update_user(user["id"], is_active=False)
    cred_id = "inactive-cc"
    await passkey_adapter.create_passkey(user["id"], cred_id, b"pk", 0, "", "Key")

    begin = await client.post(
        "/auth/passkeys/authenticate/begin",
        json={"email": "inactive@example.com"},
    )
    challenge_b64 = begin.json()["challenge"]
    client_data_json = _make_client_data_json(challenge_b64, "webauthn.get")

    credential = {
        "id": cred_id,
        "rawId": cred_id,
        "type": "public-key",
        "response": {
            "clientDataJSON": client_data_json,
            "authenticatorData": "fake",
            "signature": "fake",
        },
    }

    with patch(
        "fastauth.api.passkeys.verify_authentication_response",
        return_value=_fake_verified_authentication(),
    ):
        resp = await client.post(
            "/auth/passkeys/authenticate/complete",
            json={"credential": credential},
        )

    assert resp.status_code == 401


async def test_complete_authentication_blocked_by_hook(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client

    class BlockingHooks(EventHooks):
        async def allow_signin(self, user: UserData, provider: str) -> bool:
            return False

    app, user_adapter2, passkey_adapter2, _ = _build_app(hooks=BlockingHooks())
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        user = await user_adapter2.create_user("blocked@example.com")
        cred_id = "blocked-cred"
        await passkey_adapter2.create_passkey(user["id"], cred_id, b"pk", 0, "", "Key")

        begin = await c.post(
            "/auth/passkeys/authenticate/begin",
            json={"email": "blocked@example.com"},
        )
        challenge_b64 = begin.json()["challenge"]
        client_data_json = _make_client_data_json(challenge_b64, "webauthn.get")

        credential = {
            "id": cred_id,
            "rawId": cred_id,
            "type": "public-key",
            "response": {
                "clientDataJSON": client_data_json,
                "authenticatorData": "fake",
                "signature": "fake",
            },
        }

        with patch(
            "fastauth.api.passkeys.verify_authentication_response",
            return_value=_fake_verified_authentication(),
        ):
            resp = await c.post(
                "/auth/passkeys/authenticate/complete",
                json={"credential": credential},
            )

        assert resp.status_code == 403


async def test_complete_authentication_cookie_delivery(passkey_client):
    client, user_adapter, passkey_adapter, _ = passkey_client

    app, user_adapter2, passkey_adapter2, _ = _build_app()
    from fastauth.config import FastAuthConfig, JWTConfig
    from fastauth.providers.credentials import CredentialsProvider
    from fastauth.providers.passkey import PasskeyProvider

    user_adapter2 = MemoryUserAdapter()
    passkey_adapter2 = MemoryPasskeyAdapter()
    state_store2 = MemorySessionBackend()
    config = FastAuthConfig(
        secret="test-secret-cookie",
        providers=[
            CredentialsProvider(),
            PasskeyProvider(rp_id=RP_ID, rp_name="Test", origin=ORIGIN),
        ],
        adapter=user_adapter2,
        passkey_adapter=passkey_adapter2,
        passkey_state_store=state_store2,
        token_delivery="cookie",
        jwt=JWTConfig(algorithm="HS256"),
        debug=True,
    )
    auth = FastAuth(config)
    cookie_app = FastAPI()
    auth.mount(cookie_app)

    transport = ASGITransport(app=cookie_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        user = await user_adapter2.create_user("cookie@example.com")
        cred_id = "cookie-cred"
        await passkey_adapter2.create_passkey(user["id"], cred_id, b"pk", 0, "", "Key")

        begin = await c.post(
            "/auth/passkeys/authenticate/begin",
            json={"email": "cookie@example.com"},
        )
        challenge_b64 = begin.json()["challenge"]
        client_data_json = _make_client_data_json(challenge_b64, "webauthn.get")

        credential = {
            "id": cred_id,
            "rawId": cred_id,
            "type": "public-key",
            "response": {
                "clientDataJSON": client_data_json,
                "authenticatorData": "fake",
                "signature": "fake",
            },
        }

        with patch(
            "fastauth.api.passkeys.verify_authentication_response",
            return_value=_fake_verified_authentication(),
        ):
            resp = await c.post(
                "/auth/passkeys/authenticate/complete",
                json={"credential": credential},
            )

        assert resp.status_code == 200
        assert "access_token" in resp.cookies or "access_token" in resp.json()

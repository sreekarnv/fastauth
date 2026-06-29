import asyncio
import re
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.memory import MemoryTokenAdapter, MemoryUserAdapter
from fastauth.config import JWTConfig
from fastauth.core.one_time_tokens import (
    generate_one_time_token,
    hash_one_time_token,
)
from fastauth.email_transports.console import ConsoleTransport
from fastauth.providers.magic_links import MagicLinksProvider
from httpx import ASGITransport, AsyncClient


def test_generate_one_time_token_urlsafe_length():
    token = generate_one_time_token()
    assert isinstance(token, str)
    assert len(token) > 32


def test_hash_one_time_token_returns_hex_not_equal_to_input():
    token = generate_one_time_token()
    hashed = hash_one_time_token(token)
    assert isinstance(hashed, str)
    assert len(hashed) == 64
    assert hashed != token
    int(hashed, 16)


def test_two_distinct_tokens_hash_differently():
    a = generate_one_time_token()
    b = generate_one_time_token()
    assert a != b
    assert hash_one_time_token(a) != hash_one_time_token(b)


def test_hash_storage_directly_with_token_adapter():
    user_adapter = MemoryUserAdapter()
    token_adapter = MemoryTokenAdapter()
    raw = generate_one_time_token()
    asyncio.get_event_loop().run_until_complete(
        token_adapter.create_token(
            {
                "token": hash_one_time_token(raw),
                "user_id": "u1",
                "token_type": "magic_link_login_request",
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
                "raw_data": None,
            }
        )
    )
    stored = list(token_adapter._tokens.values())
    assert len(stored) == 1
    assert stored[0]["token"] == hash_one_time_token(raw)
    assert stored[0]["token"] != raw


def _build_magic_app(extra_config: dict | None = None):
    extra_config = extra_config or {}
    user_adapter = MemoryUserAdapter()
    token_adapter = MemoryTokenAdapter()
    config = FastAuthConfig(
        secret="this-is-a-test-secret-32-bytes!!",
        providers=[MagicLinksProvider()],
        adapter=user_adapter,
        token_adapter=token_adapter,
        jwt=JWTConfig(algorithm="HS256"),
        email_transport=ConsoleTransport(),
        base_url="http://localhost:8000",
        **extra_config,
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    return app


def _extract_token_from_capsys(capsys) -> str:
    out = capsys.readouterr().out
    for line in out.splitlines():
        if "token=" in line:
            tail = line.split("token=", 1)[1]
            raw = ""
            for ch in tail:
                if ch.isalnum() or ch in "-_.":
                    raw += ch
                else:
                    break
            if raw:
                return raw
    raise AssertionError(f"Could not find token= in console output:\n{out}")


def test_magic_link_verify_succeeds_with_raw_token(capsys):
    app = _build_magic_app()

    async def run():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            await c.post("/auth/magic-links/login", json={"email": "ok@example.com"})
            raw = _extract_token_from_capsys(capsys)
            resp = await c.get(
                f"/auth/magic-links/callback?token={raw}"
            )
            assert resp.status_code == 200
            assert "access_token" in resp.json()

    asyncio.get_event_loop().run_until_complete(run())


def test_magic_link_verify_with_wrong_token_fails():
    app = _build_magic_app()

    async def run():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            resp = await c.get(
                "/auth/magic-links/callback?token=definitely-not-a-real-token"
            )
            assert resp.status_code == 401

    asyncio.get_event_loop().run_until_complete(run())


def test_magic_link_hash_replay_fails(capsys):
    app = _build_magic_app()

    async def run():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            await c.post("/auth/magic-links/login", json={"email": "rep@example.com"})
            raw = _extract_token_from_capsys(capsys)
            hashed = hash_one_time_token(raw)

            resp_legit = await c.get(
                f"/auth/magic-links/callback?token={raw}"
            )
            assert resp_legit.status_code == 200

            resp_hash = await c.get(
                f"/auth/magic-links/callback?token={hashed}"
            )
            assert resp_hash.status_code == 401

    asyncio.get_event_loop().run_until_complete(run())

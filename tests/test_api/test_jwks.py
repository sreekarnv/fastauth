import pytest
from fastapi import FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import MemoryUserAdapter
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.providers.credentials import CredentialsProvider
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def rs256_app():
    config = FastAuthConfig(
        secret="not-used-for-rs256",
        providers=[CredentialsProvider()],
        adapter=MemoryUserAdapter(),
        jwt=JWTConfig(algorithm="RS256", jwks_enabled=True),
    )
    auth = FastAuth(config)
    await auth.initialize_jwks()

    app = FastAPI()
    auth.mount(app)
    return app


@pytest.fixture
async def rs256_client(rs256_app):
    transport = ASGITransport(app=rs256_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def hs256_app():
    config = FastAuthConfig(
        secret="test-secret-hs256",
        providers=[CredentialsProvider()],
        adapter=MemoryUserAdapter(),
        jwt=JWTConfig(algorithm="HS256"),
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    return app


@pytest.fixture
async def hs256_client(hs256_app):
    transport = ASGITransport(app=hs256_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_jwks_endpoint(rs256_client):
    resp = await rs256_client.get("/.well-known/jwks.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert len(data["keys"]) >= 1
    key = data["keys"][0]
    assert key["kty"] == "RSA"
    assert key["use"] == "sig"
    assert key["alg"] == "RS256"
    assert "d" not in key


async def test_jwks_not_mounted_hs256(hs256_client):
    resp = await hs256_client.get("/.well-known/jwks.json")
    assert resp.status_code == 404


async def test_rs256_register_and_login(rs256_client):
    resp = await rs256_client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "Password123!",
            "name": "Test",
        },
    )
    assert resp.status_code == 201
    tokens = resp.json()
    assert "access_token" in tokens

    resp = await rs256_client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "Password123!",
        },
    )
    assert resp.status_code == 200
    tokens = resp.json()

    resp = await rs256_client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert resp.status_code == 200

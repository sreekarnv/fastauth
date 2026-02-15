import pytest
from fastapi import Depends, FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import MemoryTokenAdapter, MemoryUserAdapter
from fastauth.api.deps import require_auth
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.providers.credentials import CredentialsProvider
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def memory_user_adapter():
    return MemoryUserAdapter()


@pytest.fixture
def memory_token_adapter():
    return MemoryTokenAdapter()


@pytest.fixture
def config(memory_user_adapter):
    return FastAuthConfig(
        secret="super-secret-key-only-for-testing",
        providers=[CredentialsProvider()],
        adapter=memory_user_adapter,
        jwt=JWTConfig(
            algorithm="HS256", access_token_ttl=900, refresh_token_ttl=2_592_000
        ),
    )


@pytest.fixture
def auth(config):
    return FastAuth(config)


@pytest.fixture
def app(auth):

    _app = FastAPI()
    auth.mount(_app)

    @_app.get("/protected")
    async def protected_route(user=Depends(require_auth)):
        return {"user": user, "message": "protected_router loaded"}

    return _app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

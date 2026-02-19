import pytest
from fastauth.adapters.memory import MemorySessionAdapter
from fastauth.session_backends.database import DatabaseSessionBackend


@pytest.fixture
def session_adapter():
    return MemorySessionAdapter()


@pytest.fixture
def backend(session_adapter):
    return DatabaseSessionBackend(session_adapter)


async def test_write_and_read(backend):
    await backend.write("s1", {"user_id": "u1"}, ttl=3600)
    data = await backend.read("s1")
    assert data is not None
    assert data["user_id"] == "u1"


async def test_read_nonexistent(backend):
    result = await backend.read("missing")
    assert result is None


async def test_delete(backend):
    await backend.write("s1", {"user_id": "u1"}, ttl=3600)
    await backend.delete("s1")
    result = await backend.read("s1")
    assert result is None


async def test_exists_true(backend):
    await backend.write("s1", {"user_id": "u1"}, ttl=3600)
    assert await backend.exists("s1") is True


async def test_exists_false(backend):
    assert await backend.exists("missing") is False


async def test_write_with_ip_and_agent(backend):
    await backend.write(
        "s2",
        {"user_id": "u2", "ip_address": "127.0.0.1", "user_agent": "test-agent"},
        ttl=3600,
    )
    data = await backend.read("s2")
    assert data is not None
    assert data["user_id"] == "u2"

import time
from unittest.mock import patch

from fastauth.session_backends.memory import MemorySessionBackend


async def test_write_and_read():
    backend = MemorySessionBackend()
    await backend.write("s1", {"user_id": "u1"}, ttl=3600)
    data = await backend.read("s1")
    assert data == {"user_id": "u1"}


async def test_read_nonexistent():
    backend = MemorySessionBackend()
    assert await backend.read("missing") is None


async def test_read_expired():
    backend = MemorySessionBackend()
    await backend.write("s1", {"user_id": "u1"}, ttl=1)
    with patch("fastauth.session_backends.memory.time") as mock_time:
        mock_time.time.return_value = time.time() + 10
        assert await backend.read("s1") is None


async def test_delete():
    backend = MemorySessionBackend()
    await backend.write("s1", {"user_id": "u1"}, ttl=3600)
    await backend.delete("s1")
    assert await backend.read("s1") is None


async def test_exists():
    backend = MemorySessionBackend()
    assert await backend.exists("s1") is False
    await backend.write("s1", {"user_id": "u1"}, ttl=3600)
    assert await backend.exists("s1") is True


async def test_overwrite():
    backend = MemorySessionBackend()
    await backend.write("s1", {"user_id": "u1"}, ttl=3600)
    await backend.write("s1", {"user_id": "u2"}, ttl=3600)
    data = await backend.read("s1")
    assert data is not None
    assert "user_id" in data and data["user_id"] == "u2"

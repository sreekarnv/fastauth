import json
from unittest.mock import AsyncMock, patch

import pytest
from fastauth.session_backends.redis import RedisSessionBackend


@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.setex = AsyncMock()
    r.delete = AsyncMock()
    r.exists = AsyncMock(return_value=0)
    return r


@pytest.fixture
def backend(mock_redis):
    with patch("fastauth._compat.require", return_value=None):
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            b = RedisSessionBackend(url="redis://localhost:6379")
    b._redis = mock_redis
    return b


async def test_read_nonexistent(backend, mock_redis):
    mock_redis.get.return_value = None
    result = await backend.read("s1")
    assert result is None


async def test_read_existing(backend, mock_redis):
    mock_redis.get.return_value = json.dumps({"user_id": "u1"}).encode()
    result = await backend.read("s1")
    assert result == {"user_id": "u1"}


async def test_write(backend, mock_redis):
    await backend.write("s1", {"user_id": "u1"}, ttl=3600)
    mock_redis.setex.assert_called_once()
    args = mock_redis.setex.call_args
    assert "fastauth:session:s1" in args[0]
    assert args[0][1] == 3600


async def test_delete(backend, mock_redis):
    await backend.delete("s1")
    mock_redis.delete.assert_called_once_with("fastauth:session:s1")


async def test_exists_false(backend, mock_redis):
    mock_redis.exists.return_value = 0
    assert await backend.exists("s1") is False


async def test_exists_true(backend, mock_redis):
    mock_redis.exists.return_value = 1
    assert await backend.exists("s1") is True


def test_key_format(backend):
    assert backend._key("abc") == "fastauth:session:abc"

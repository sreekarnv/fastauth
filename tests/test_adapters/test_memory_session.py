from datetime import datetime, timedelta, timezone

from fastauth.adapters.memory import MemorySessionAdapter
from fastauth.types import SessionData


def _make_session(
    sid: str = "s1", user_id: str = "u1", hours: int = 1
) -> SessionData:
    return SessionData(
        id=sid,
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=hours),
        ip_address="127.0.0.1",
        user_agent="test",
    )


async def test_create_and_get():
    adapter = MemorySessionAdapter()
    session = _make_session()
    result = await adapter.create_session(session)
    assert result["id"] == "s1"

    fetched = await adapter.get_session("s1")
    assert fetched is not None
    assert fetched["user_id"] == "u1"


async def test_get_nonexistent():
    adapter = MemorySessionAdapter()
    assert await adapter.get_session("missing") is None


async def test_get_expired():
    adapter = MemorySessionAdapter()
    session = _make_session(hours=-1)
    await adapter.create_session(session)
    assert await adapter.get_session("s1") is None


async def test_delete():
    adapter = MemorySessionAdapter()
    await adapter.create_session(_make_session())
    await adapter.delete_session("s1")
    assert await adapter.get_session("s1") is None


async def test_delete_user_sessions():
    adapter = MemorySessionAdapter()
    await adapter.create_session(_make_session("s1", "u1"))
    await adapter.create_session(_make_session("s2", "u1"))
    await adapter.create_session(_make_session("s3", "u2"))

    await adapter.delete_user_sessions("u1")

    assert await adapter.get_session("s1") is None
    assert await adapter.get_session("s2") is None
    assert await adapter.get_session("s3") is not None


async def test_cleanup_expired():
    adapter = MemorySessionAdapter()
    await adapter.create_session(_make_session("s1", "u1", hours=1))
    await adapter.create_session(_make_session("s2", "u1", hours=-1))
    await adapter.create_session(_make_session("s3", "u2", hours=-2))

    count = await adapter.cleanup_expired()
    assert count == 2
    assert await adapter.get_session("s1") is not None

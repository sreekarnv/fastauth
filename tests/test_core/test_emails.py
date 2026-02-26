import textwrap
from unittest.mock import AsyncMock

import pytest

jinja2 = pytest.importorskip("jinja2")

from fastauth.core.emails import EmailDispatcher  # noqa: E402


@pytest.fixture
def mock_transport():
    transport = AsyncMock()
    transport.send = AsyncMock()
    return transport


@pytest.fixture
def dispatcher(mock_transport):
    return EmailDispatcher(
        transport=mock_transport,
        base_url="http://localhost:8000",
    )


@pytest.fixture
def user():
    return {
        "id": "user1",
        "email": "test@example.com",
        "name": "Test User",
        "image": None,
        "email_verified": False,
        "is_active": True,
    }


async def test_send_verification_email(dispatcher, mock_transport, user):
    await dispatcher.send_verification_email(user, "tok123", 60)
    mock_transport.send.assert_called_once()
    call_kwargs = mock_transport.send.call_args.kwargs
    assert call_kwargs["to"] == "test@example.com"
    assert "Verify" in call_kwargs["subject"]
    assert "tok123" in call_kwargs["body_html"]


async def test_send_password_reset_email(dispatcher, mock_transport, user):
    await dispatcher.send_password_reset_email(user, "reset_tok", 30)
    mock_transport.send.assert_called_once()
    call_kwargs = mock_transport.send.call_args.kwargs
    assert call_kwargs["to"] == "test@example.com"
    assert "Reset" in call_kwargs["subject"] or "reset" in call_kwargs["subject"]
    assert "reset_tok" in call_kwargs["body_html"]


async def test_send_welcome_email(dispatcher, mock_transport, user):
    await dispatcher.send_welcome_email(user)
    mock_transport.send.assert_called_once()
    call_kwargs = mock_transport.send.call_args.kwargs
    assert call_kwargs["to"] == "test@example.com"
    assert "Welcome" in call_kwargs["subject"]


async def test_send_magic_link_login_email(dispatcher, mock_transport, user):
    await dispatcher.send_magic_link_login_request(user, "ml_tok_abc")
    mock_transport.send.assert_called_once()
    call_kwargs = mock_transport.send.call_args.kwargs
    assert call_kwargs["to"] == "test@example.com"
    assert "ml_tok_abc" in call_kwargs["body_html"]


async def test_custom_template_overrides_builtin(mock_transport, user, tmp_path):
    # Write a custom welcome template into a temp dir
    custom = tmp_path / "welcome.jinja2"
    custom.write_text(
        textwrap.dedent("""\
            <p>CUSTOM WELCOME {{ name }}</p>
        """)
    )
    dispatcher = EmailDispatcher(
        transport=mock_transport,
        base_url="http://localhost:8000",
        template_dir=tmp_path,
    )
    await dispatcher.send_welcome_email(user)
    body = mock_transport.send.call_args.kwargs["body_html"]
    assert "CUSTOM WELCOME" in body
    assert "Test User" in body


async def test_non_overridden_template_falls_back_to_builtin(
    mock_transport, user, tmp_path
):
    # template_dir exists but contains no welcome.jinja2
    dispatcher = EmailDispatcher(
        transport=mock_transport,
        base_url="http://localhost:8000",
        template_dir=tmp_path,
    )
    await dispatcher.send_welcome_email(user)
    body = mock_transport.send.call_args.kwargs["body_html"]
    # Built-in template renders the user's name
    assert "Test User" in body


async def test_noop_when_no_transport(user):
    dispatcher = EmailDispatcher(transport=None, base_url="http://localhost")
    await dispatcher.send_verification_email(user, "tok", 60)
    await dispatcher.send_password_reset_email(user, "tok", 30)
    await dispatcher.send_welcome_email(user)
    await dispatcher.send_email_change_email(user, "new@example.com", "tok", 30)
    await dispatcher.send_magic_link_login_request(user, "tok")

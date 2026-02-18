import pytest
from fastauth.email_transports.console import ConsoleTransport


@pytest.fixture
def transport():
    return ConsoleTransport()


async def test_send_prints_html(transport, capsys):
    await transport.send(
        to="user@example.com",
        subject="Test Subject",
        body_html="<h1>Hello</h1>",
    )
    captured = capsys.readouterr()
    assert "user@example.com" in captured.out
    assert "Test Subject" in captured.out
    assert "<h1>Hello</h1>" in captured.out


async def test_send_prints_text_when_provided(transport, capsys):
    await transport.send(
        to="user@example.com",
        subject="Test",
        body_html="<h1>Hello</h1>",
        body_text="Hello plain",
    )
    captured = capsys.readouterr()
    assert "Hello plain" in captured.out

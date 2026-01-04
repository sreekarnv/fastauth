"""
Additional tests for auth API endpoints to achieve full coverage.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_register_rate_limit_exceeded(client: TestClient):
    """Test registration rate limiting."""
    from fastauth.security import limits

    limits.register_rate_limiter._store.clear()

    original_max_attempts = limits.register_rate_limiter.max_attempts
    limits.register_rate_limiter.max_attempts = 2

    try:
        client.post(
            "/auth/register",
            json={"email": "test1@example.com", "password": "password123"},
        )
        client.post(
            "/auth/register",
            json={"email": "test2@example.com", "password": "password123"},
        )

        response = client.post(
            "/auth/register",
            json={"email": "test3@example.com", "password": "password123"},
        )

        assert response.status_code == 429
        assert "Too many" in response.json()["detail"]

    finally:
        limits.register_rate_limiter.max_attempts = original_max_attempts
        limits.register_rate_limiter._store.clear()


def test_login_rate_limit_exceeded(client: TestClient):
    """Test login rate limiting."""
    from fastauth.security import limits

    limits.login_rate_limiter._store.clear()

    client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password123"}
    )

    original_max_attempts = limits.login_rate_limiter.max_attempts
    limits.login_rate_limiter.max_attempts = 2

    try:
        client.post(
            "/auth/login", json={"email": "test@example.com", "password": "wrong1"}
        )
        client.post(
            "/auth/login", json={"email": "test@example.com", "password": "wrong2"}
        )

        response = client.post(
            "/auth/login", json={"email": "test@example.com", "password": "wrong3"}
        )

        assert response.status_code == 429
        assert "Too many" in response.json()["detail"]

    finally:
        limits.login_rate_limiter.max_attempts = original_max_attempts
        limits.login_rate_limiter._store.clear()


def test_refresh_token_endpoint_success(client: TestClient):
    """Test successful token refresh."""
    response = client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    refresh_token = response.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_endpoint_invalid_token(client: TestClient):
    """Test token refresh with invalid token."""
    response = client.post("/auth/refresh", json={"refresh_token": "invalid_token_123"})

    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_logout_endpoint(client: TestClient):
    """Test logout endpoint."""
    response = client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password123"}
    )
    refresh_token = response.json()["refresh_token"]

    response = client.post("/auth/logout", json={"refresh_token": refresh_token})

    assert response.status_code == 204


def test_password_reset_request(client: TestClient, capsys):
    """Test password reset request endpoint."""
    client.post(
        "/auth/register", json={"email": "reset@example.com", "password": "password123"}
    )

    response = client.post(
        "/auth/password-reset/request", json={"email": "reset@example.com"}
    )

    assert response.status_code == 204

    captured = capsys.readouterr()
    assert "Password reset token:" in captured.out


def test_password_reset_request_nonexistent_email(client: TestClient):
    """
    Test password reset for nonexistent email.
    Should still return 204 for security.
    """
    response = client.post(
        "/auth/password-reset/request", json={"email": "nonexistent@example.com"}
    )

    assert response.status_code == 204


@patch("fastauth.api.auth.get_email_client")
def test_password_reset_request_with_email_client(mock_get_client, client: TestClient):
    """Test that password reset sends email via email client."""
    from unittest.mock import MagicMock

    mock_email_client = MagicMock()
    mock_get_client.return_value = mock_email_client

    client.post(
        "/auth/register", json={"email": "reset@example.com", "password": "password123"}
    )

    response = client.post(
        "/auth/password-reset/request", json={"email": "reset@example.com"}
    )

    assert response.status_code == 204
    assert mock_email_client.send_password_reset_email.called


def test_password_reset_confirm_success(client: TestClient, capsys):
    """Test successful password reset confirmation."""
    client.post(
        "/auth/register",
        json={"email": "reset@example.com", "password": "old_password"},
    )

    client.post("/auth/password-reset/request", json={"email": "reset@example.com"})

    captured = capsys.readouterr()
    import re

    match = re.search(r"Password reset token: (\S+)", captured.out)
    assert match
    token = match.group(1)

    response = client.post(
        "/auth/password-reset/confirm",
        json={"token": token, "new_password": "new_password123"},
    )

    assert response.status_code == 204

    response = client.post(
        "/auth/login",
        json={"email": "reset@example.com", "password": "new_password123"},
    )
    assert response.status_code == 200


def test_password_reset_confirm_invalid_token(client: TestClient):
    """Test password reset confirmation with invalid token."""
    response = client.post(
        "/auth/password-reset/confirm",
        json={"token": "invalid_token", "new_password": "new_password"},
    )

    assert response.status_code == 400
    assert "Invalid or expired" in response.json()["detail"]


def test_email_verification_request(client: TestClient, capsys):
    """Test email verification request endpoint."""
    client.post(
        "/auth/register",
        json={"email": "verify@example.com", "password": "password123"},
    )

    response = client.post(
        "/auth/email-verification/request", json={"email": "verify@example.com"}
    )

    assert response.status_code == 204
    captured = capsys.readouterr()
    assert "Email verification token:" in captured.out


def test_email_verification_request_nonexistent_email(client: TestClient):
    """Test email verification for nonexistent email."""
    response = client.post(
        "/auth/email-verification/request", json={"email": "nonexistent@example.com"}
    )

    assert response.status_code == 204


@patch("fastauth.api.auth.get_email_client")
def test_email_verification_request_with_email_client(
    mock_get_client, client: TestClient
):
    """Test that email verification sends email via email client."""
    from unittest.mock import MagicMock

    mock_email_client = MagicMock()
    mock_get_client.return_value = mock_email_client

    client.post(
        "/auth/register",
        json={"email": "verify@example.com", "password": "password123"},
    )

    response = client.post(
        "/auth/email-verification/request", json={"email": "verify@example.com"}
    )

    assert response.status_code == 204
    assert mock_email_client.send_verification_email.called


def test_email_verification_confirm_success(client: TestClient, capsys):
    """Test successful email verification confirmation."""
    client.post(
        "/auth/register",
        json={"email": "verify@example.com", "password": "password123"},
    )

    captured = capsys.readouterr()
    import re

    match = re.search(r"Email verification token for .+?: (\S+)", captured.out)
    assert match
    token = match.group(1)

    response = client.post("/auth/email-verification/confirm", json={"token": token})

    assert response.status_code == 204


def test_email_verification_confirm_invalid_token(client: TestClient):
    """Test email verification confirmation with invalid token."""
    response = client.post(
        "/auth/email-verification/confirm", json={"token": "invalid_token"}
    )

    assert response.status_code == 400
    assert "Invalid or expired" in response.json()["detail"]


def test_resend_email_verification(client: TestClient, capsys):
    """Test resending email verification."""
    client.post(
        "/auth/register",
        json={"email": "resend@example.com", "password": "password123"},
    )

    response = client.post(
        "/auth/email-verification/resend", json={"email": "resend@example.com"}
    )

    assert response.status_code == 204
    captured = capsys.readouterr()
    assert "Resent email verification token:" in captured.out


def test_resend_email_verification_rate_limit(client: TestClient):
    """Test resend email verification rate limiting."""
    from fastauth.security import limits

    limits.email_verification_rate_limiter._store.clear()
    client.post(
        "/auth/register",
        json={"email": "resend@example.com", "password": "password123"},
    )

    original_max_attempts = limits.email_verification_rate_limiter.max_attempts
    limits.email_verification_rate_limiter.max_attempts = 2

    try:
        client.post(
            "/auth/email-verification/resend", json={"email": "resend@example.com"}
        )
        client.post(
            "/auth/email-verification/resend", json={"email": "resend@example.com"}
        )

        response = client.post(
            "/auth/email-verification/resend", json={"email": "resend@example.com"}
        )

        assert response.status_code == 429
        assert "Too many" in response.json()["detail"]

    finally:
        limits.email_verification_rate_limiter.max_attempts = original_max_attempts
        limits.email_verification_rate_limiter._store.clear()


@patch("fastauth.api.auth.get_email_client")
def test_resend_email_verification_with_email_client(
    mock_get_client, client: TestClient
):
    """Test that resend email verification sends email via email client."""
    from unittest.mock import MagicMock

    mock_email_client = MagicMock()
    mock_get_client.return_value = mock_email_client

    client.post(
        "/auth/register",
        json={"email": "resend@example.com", "password": "password123"},
    )

    response = client.post(
        "/auth/email-verification/resend", json={"email": "resend@example.com"}
    )

    assert response.status_code == 204
    assert mock_email_client.send_verification_email.called


@patch("fastauth.api.auth.get_email_client")
def test_register_sends_verification_email(mock_get_client, client: TestClient):
    """Test that registration sends verification email."""
    from unittest.mock import MagicMock

    mock_email_client = MagicMock()
    mock_get_client.return_value = mock_email_client

    response = client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password123"}
    )

    assert response.status_code == 200
    assert mock_email_client.send_verification_email.called

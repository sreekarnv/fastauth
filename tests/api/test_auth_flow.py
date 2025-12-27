from fastapi.testclient import TestClient


def test_register_user(client: TestClient):
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client: TestClient):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )

    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "different_password"}
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_login_success(client: TestClient):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )

    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_email(client: TestClient):
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"}
    )

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_login_invalid_password(client: TestClient):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )

    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrong_password"}
    )

    assert response.status_code == 401


def test_login_unverified_email(client: TestClient):
    import os
    os.environ["REQUIRE_EMAIL_VERIFICATION"] = "true"

    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )

    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )

    assert response.status_code == 403
    assert "not verified" in response.json()["detail"].lower()


def test_login_missing_fields(client: TestClient):
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com"}
    )

    assert response.status_code == 422


def test_register_missing_fields(client: TestClient):
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com"}
    )

    assert response.status_code == 422


def test_register_invalid_email(client: TestClient):
    response = client.post(
        "/auth/register",
        json={"email": "invalid-email", "password": "password123"}
    )

    assert response.status_code == 422

from fastapi.testclient import TestClient


def test_full_registration_and_login_flow(client: TestClient):
    register_response = client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password123"}
    )
    assert register_response.status_code == 200
    assert "access_token" in register_response.json()
    assert "refresh_token" in register_response.json()

    login_response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "password123"}
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
    assert "refresh_token" in login_response.json()


def test_full_token_refresh_flow(client: TestClient):
    register_response = client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password123"}
    )
    refresh_token = register_response.json()["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()
    new_refresh_token = refresh_response.json()["refresh_token"]
    assert new_refresh_token != refresh_token


def test_logout_invalidates_refresh_token(client: TestClient):
    register_response = client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password123"}
    )
    refresh_token = register_response.json()["refresh_token"]

    logout_response = client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert logout_response.status_code == 204

    reuse_response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_response.status_code == 401

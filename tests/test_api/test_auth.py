import pytest


@pytest.fixture
def user():
    return {"email": "text@example.com", "name": "Test User", "password": "Pass123#"}


async def __register_user(client, email="test@example.com", password="Pass123#"):
    data = {"email": email, "password": password, "name": "Test User"}
    resp = await client.post("/auth/register", json=data)
    return resp


async def __login_user(client, email="test@example.com", password="Pass123#"):
    data = {"email": email, "password": password}
    resp = await client.post("/auth/login", json=data)
    return resp


async def __refresh(client, refresh_token: str):
    data = {"refresh_token": refresh_token}
    resp = await client.post("/auth/refresh", json=data)
    return resp


async def __logout(client, headers=None):
    resp = await client.post("/auth/logout", headers=headers)
    return resp


async def __protected(client, headers=None):
    resp = await client.get("/protected", headers=headers)
    return resp


async def test_register_success(client):
    resp = await __register_user(client)
    data = resp.json()

    assert resp.status_code == 201
    assert "access_token" in data
    assert "refresh_token" in data
    assert "expires_in" in data
    assert "token_type" in data and data["token_type"] == "bearer"


async def test_register_duplicate_email(client):
    _resp = await __register_user(client)
    assert _resp.status_code == 201

    _resp = await __register_user(client)
    assert _resp.status_code == 409


async def test_register_invalid_email(client):
    _resp = await __register_user(client, email="random-text")
    assert _resp.status_code == 422


async def test_login_success(client):
    register_resp = await __register_user(client)
    assert register_resp.status_code == 201

    resp = await __login_user(client)
    data = resp.json()

    assert resp.status_code == 200
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client, user):
    await __register_user(client, user["email"], user["password"])
    resp = await __login_user(client, email=user["email"], password="wrong-password")

    assert resp.status_code == 401


async def test_login_nonexistent_user(client, user):
    resp = await __login_user(client, email=user["email"], password="wrong-password")
    assert resp.status_code == 401


async def test_refresh_success(client):
    resp = await __register_user(client)
    data = resp.json()

    _resp = await __refresh(client, refresh_token=data["refresh_token"])
    assert _resp.status_code == 200


async def test_refresh_invalid_token(client):
    await __register_user(client)

    _resp = await __refresh(client, refresh_token="garbage")
    assert _resp.status_code == 401


async def test_refresh_with_access_token(client):
    r = await __register_user(client)
    data = r.json()

    _resp = await __refresh(client, refresh_token=data["access_token"])
    assert _resp.status_code == 401


async def test_logout_success(client):
    r = await __register_user(client)
    data = r.json()

    _resp = await __logout(
        client, headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert _resp.status_code == 200
    assert _resp.json()["message"] == "Logged out"


async def test_logout_unauthenticated(client):
    _resp = await __logout(client)
    assert _resp.status_code == 401


async def test_protected_route_with_token(client):
    r = await __register_user(client)
    data = r.json()
    access_token = data["access_token"]

    resp = await __protected(
        client, headers={"Authorization": f"Bearer {access_token}"}
    )
    data = resp.json()
    assert resp.status_code == 200
    assert "message" in data and data["message"] == "protected_router loaded"

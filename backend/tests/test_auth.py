import pytest

@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePass123!",
        "display_name": "Test User"
    })
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["tier"] == "free"

@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dupe@example.com", "username": "user1", "password": "SecurePass123!"}
    await client.post("/api/v1/auth/register", json=payload)
    payload["username"] = "user2"
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code in (400, 409)

@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com", "username": "loginuser", "password": "SecurePass123!"
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com", "password": "SecurePass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com", "username": "wronguser", "password": "SecurePass123!"
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com", "password": "WrongPassword!"
    })
    assert response.status_code in (400, 401)

@pytest.mark.asyncio
async def test_protected_route_no_auth(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)

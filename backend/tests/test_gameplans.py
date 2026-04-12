import pytest

async def get_auth_token(client):
    await client.post("/api/v1/auth/register", json={
        "email": "gp@example.com", "username": "gpuser", "password": "SecurePass123!"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "gp@example.com", "password": "SecurePass123!"
    })
    return resp.json()["access_token"]

@pytest.mark.asyncio
async def test_list_gameplans_empty(client):
    token = await get_auth_token(client)
    response = await client.get("/api/v1/gameplans", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []

@pytest.mark.asyncio
async def test_gameplans_requires_auth(client):
    response = await client.get("/api/v1/gameplans")
    assert response.status_code in (401, 403)

"""Integration tests for the authentication flow (register / login / me)."""

import pytest
from httpx import AsyncClient

# --------------------------------------------------------------------------
# Test data
# --------------------------------------------------------------------------
VALID_USER = {
    "email": "forge_tester@example.com",
    "username": "forge_tester",
    "password": "Str0ngP@ssw0rd!",
    "display_name": "Forge Tester",
}

SECOND_USER = {
    "email": "second_user@example.com",
    "username": "second_user",
    "password": "An0therP@ss!",
}


class TestRegister:
    """POST /api/v1/auth/register."""

    async def test_register_valid_user(self, test_client: AsyncClient):
        response = await test_client.post("/api/v1/auth/register", json=VALID_USER)
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["email"] == VALID_USER["email"]
        assert data["username"] == VALID_USER["username"]
        assert "id" in data

    async def test_register_duplicate_email(self, test_client: AsyncClient):
        # First registration succeeds.
        await test_client.post("/api/v1/auth/register", json=VALID_USER)
        # Duplicate email should be rejected.
        duplicate = {**VALID_USER, "username": "different_name"}
        response = await test_client.post("/api/v1/auth/register", json=duplicate)
        assert response.status_code in (400, 409)

    async def test_register_duplicate_username(self, test_client: AsyncClient):
        await test_client.post("/api/v1/auth/register", json=VALID_USER)
        duplicate = {**VALID_USER, "email": "other@example.com"}
        response = await test_client.post("/api/v1/auth/register", json=duplicate)
        assert response.status_code in (400, 409)

    async def test_register_missing_fields(self, test_client: AsyncClient):
        response = await test_client.post("/api/v1/auth/register", json={})
        assert response.status_code == 422


class TestLogin:
    """POST /api/v1/auth/login."""

    async def test_login_correct_credentials(self, test_client: AsyncClient):
        await test_client.post("/api/v1/auth/register", json=VALID_USER)
        response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data.get("token_type") == "bearer"

    async def test_login_wrong_password(self, test_client: AsyncClient):
        await test_client.post("/api/v1/auth/register", json=VALID_USER)
        response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": "WrongPassword123!"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_email(self, test_client: AsyncClient):
        response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "irrelevant"},
        )
        assert response.status_code == 401


class TestMe:
    """GET /api/v1/auth/me."""

    async def test_me_with_valid_token(self, test_client: AsyncClient):
        # Register + login to obtain a token.
        await test_client.post("/api/v1/auth/register", json=VALID_USER)
        login_resp = await test_client.post(
            "/api/v1/auth/login",
            json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
        )
        token = login_resp.json()["access_token"]

        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == VALID_USER["email"]
        assert data["username"] == VALID_USER["username"]

    async def test_me_without_token(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)

    async def test_me_with_invalid_token(self, test_client: AsyncClient):
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        assert response.status_code in (401, 403)

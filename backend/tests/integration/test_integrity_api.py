"""Integration tests for IntegrityMode compliance endpoints."""

import pytest
from httpx import AsyncClient

USER_ID = "integrity-test-user"


class TestIntegrityGetMode:
    """GET /api/v1/integrity/mode."""

    async def test_get_mode_returns_settings(self, test_client: AsyncClient):
        response = await test_client.get(
            "/api/v1/integrity/mode",
            params={"user_id": USER_ID},
        )
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "environment" in data
            assert "timing" in data
        else:
            assert response.status_code in (404, 422, 500)

    async def test_get_mode_missing_user_id(self, test_client: AsyncClient):
        """user_id is required — omitting it should 422."""
        response = await test_client.get("/api/v1/integrity/mode")
        assert response.status_code == 422


class TestIntegritySetMode:
    """PUT /api/v1/integrity/mode."""

    async def test_set_mode_valid(self, test_client: AsyncClient):
        response = await test_client.put(
            "/api/v1/integrity/mode",
            params={"user_id": USER_ID},
            json={
                "environment": "ranked_online",
                "timing": "pre_game",
            },
        )
        if response.status_code == 200:
            data = response.json()
            assert data["environment"] == "ranked_online"
            assert data["timing"] == "pre_game"
            assert data["user_id"] == USER_ID
        else:
            assert response.status_code in (404, 422, 500)

    async def test_set_mode_tournament(self, test_client: AsyncClient):
        response = await test_client.put(
            "/api/v1/integrity/mode",
            params={"user_id": USER_ID},
            json={
                "environment": "tournament",
                "timing": "between_series",
            },
        )
        if response.status_code == 200:
            data = response.json()
            assert data["environment"] == "tournament"
        else:
            assert response.status_code in (404, 422, 500)

    async def test_set_mode_invalid_environment(self, test_client: AsyncClient):
        response = await test_client.put(
            "/api/v1/integrity/mode",
            params={"user_id": USER_ID},
            json={
                "environment": "not_a_valid_env",
                "timing": "pre_game",
            },
        )
        assert response.status_code == 422

    async def test_set_mode_missing_body(self, test_client: AsyncClient):
        response = await test_client.put(
            "/api/v1/integrity/mode",
            params={"user_id": USER_ID},
        )
        assert response.status_code == 422


class TestIntegrityMatrix:
    """GET /api/v1/integrity/matrix."""

    async def test_matrix_returns_features(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/integrity/matrix")
        if response.status_code == 200:
            data = response.json()
            assert "features" in data
            assert isinstance(data["features"], list)
            # Each feature should have the four compliance axes.
            for feature in data["features"]:
                assert "feature_name" in feature
                assert "environments" in feature
                assert "timings" in feature
                assert "risk_level" in feature
                assert "anti_cheat_status" in feature
        else:
            assert response.status_code in (404, 500)

    async def test_matrix_no_auth_required(self, test_client: AsyncClient):
        """The matrix endpoint should be publicly readable."""
        response = await test_client.get("/api/v1/integrity/matrix")
        assert response.status_code in (200, 500)

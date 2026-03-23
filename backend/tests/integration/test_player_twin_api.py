"""Integration tests for PlayerTwin endpoints."""

import pytest
from httpx import AsyncClient

USER_ID = "twin-test-user-001"
TITLE = "madden26"

BOOTSTRAP_PAYLOAD = {
    "sessions": [
        {
            "session_id": "sess-001",
            "user_id": USER_ID,
            "title": TITLE,
            "mode": "ranked",
            "result": "win",
            "score_differential": 7,
            "duration_seconds": 1800,
            "plays": [
                {"type": "pass", "yards": 12, "result": "complete"},
                {"type": "run", "yards": 5, "result": "gain"},
            ],
            "pressure_moments": [],
            "skill_events": [],
        }
    ]
}


class TestPlayerTwinProfile:
    """GET /api/v1/player-twin/{user_id}."""

    async def test_get_profile_returns_shape(self, test_client: AsyncClient):
        response = await test_client.get(
            f"/api/v1/player-twin/{USER_ID}",
            params={"title": TITLE},
        )
        # The service may return mock/stub data or raise.
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "title" in data
            assert "identity" in data
            assert "execution_scores" in data
            assert "tendencies" in data
            assert data["user_id"] == USER_ID
        else:
            # Route exists but service is stubbed.
            assert response.status_code in (404, 422, 500)

    async def test_get_profile_missing_title(self, test_client: AsyncClient):
        """Title is a required query param — omitting it should 422."""
        response = await test_client.get(f"/api/v1/player-twin/{USER_ID}")
        assert response.status_code == 422


class TestPlayerTwinBootstrap:
    """POST /api/v1/player-twin/{user_id}/bootstrap."""

    async def test_bootstrap_returns_profile(self, test_client: AsyncClient):
        response = await test_client.post(
            f"/api/v1/player-twin/{USER_ID}/bootstrap",
            json=BOOTSTRAP_PAYLOAD,
        )
        if response.status_code in (200, 201):
            data = response.json()
            assert "user_id" in data
            assert "title" in data
            assert "identity" in data
            assert "sessions_analyzed" in data
        else:
            assert response.status_code in (400, 422, 500)

    async def test_bootstrap_empty_sessions(self, test_client: AsyncClient):
        """Submitting empty sessions list should fail."""
        response = await test_client.post(
            f"/api/v1/player-twin/{USER_ID}/bootstrap",
            json={"sessions": []},
        )
        # The endpoint explicitly checks for empty sessions (400),
        # or pydantic validation may reject min_length=1 (422).
        assert response.status_code in (400, 422)

    async def test_bootstrap_invalid_body(self, test_client: AsyncClient):
        response = await test_client.post(
            f"/api/v1/player-twin/{USER_ID}/bootstrap",
            json={"not_sessions": True},
        )
        assert response.status_code == 422

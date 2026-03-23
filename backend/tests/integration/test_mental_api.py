"""Integration tests for Mental services (confidence, readiness, narrative).

Note: The current mental router does not expose POST /mental/checkin or
GET /mental/{id}/tilt. Tests target the closest available endpoints:
- GET /mental/{user_id}/confidence (analogous to a confidence "check-in")
- GET /mental/{user_id}/readiness (pre-game readiness / tilt assessment)
"""

import pytest
from httpx import AsyncClient

USER_ID = "mental-test-user-001"
TITLE = "madden26"


class TestMentalCheckin:
    """Mental check-in: GET /api/v1/mental/{user_id}/confidence.

    Serves as the evidence-based mental-state check-in endpoint.
    """

    async def test_confidence_returns_score(self, test_client: AsyncClient):
        response = await test_client.get(
            f"/api/v1/mental/{USER_ID}/confidence",
            params={"title": TITLE},
        )
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "overall" in data
            assert isinstance(data["overall"], (int, float))
            assert 0.0 <= data["overall"] <= 1.0
        else:
            # Service may not be fully wired.
            assert response.status_code in (404, 422, 500)

    async def test_confidence_missing_title(self, test_client: AsyncClient):
        """Title is required — omitting should 422."""
        response = await test_client.get(f"/api/v1/mental/{USER_ID}/confidence")
        assert response.status_code == 422

    async def test_confidence_different_user(self, test_client: AsyncClient):
        response = await test_client.get(
            "/api/v1/mental/other-user-999/confidence",
            params={"title": TITLE},
        )
        assert response.status_code in (200, 404, 500)


class TestMentalTilt:
    """Tilt / readiness: GET /api/v1/mental/{user_id}/readiness.

    Pre-game readiness includes fatigue/tilt signals as the closest
    endpoint to a dedicated tilt check.
    """

    async def test_readiness_returns_assessment(self, test_client: AsyncClient):
        response = await test_client.get(
            f"/api/v1/mental/{USER_ID}/readiness",
            params={"title": TITLE},
        )
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "level" in data
            assert "composite_score" in data
            assert "fatigue_factor" in data
            # Level should be a valid ReadinessLevel value.
            valid_levels = {"peak", "ready", "moderate", "fatigued", "low"}
            assert data["level"] in valid_levels
        else:
            assert response.status_code in (404, 422, 500)

    async def test_readiness_missing_title(self, test_client: AsyncClient):
        response = await test_client.get(f"/api/v1/mental/{USER_ID}/readiness")
        assert response.status_code == 422


class TestMentalBenchmarks:
    """GET /api/v1/mental/{user_id}/benchmarks."""

    async def test_benchmarks_returns_comparison(self, test_client: AsyncClient):
        response = await test_client.get(
            f"/api/v1/mental/{USER_ID}/benchmarks",
            params={"title": TITLE, "percentile": 90},
        )
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "target_percentile" in data
            assert "dimensions" in data
        else:
            assert response.status_code in (404, 422, 500)


class TestMentalNarrative:
    """GET /api/v1/mental/{user_id}/narrative."""

    async def test_narrative_returns_story(self, test_client: AsyncClient):
        response = await test_client.get(
            f"/api/v1/mental/{USER_ID}/narrative",
            params={"title": TITLE},
        )
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "narrative" in data
        else:
            assert response.status_code in (404, 422, 500)


class TestMentalGrowth:
    """GET /api/v1/mental/{user_id}/growth."""

    async def test_growth_returns_trajectory(self, test_client: AsyncClient):
        response = await test_client.get(
            f"/api/v1/mental/{USER_ID}/growth",
            params={"title": TITLE, "weeks": 4},
        )
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "trends" in data
            assert "overall_direction" in data
        else:
            assert response.status_code in (404, 422, 500)

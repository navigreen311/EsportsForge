"""Integration tests for health and platform status endpoints."""

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """GET /api/health — basic liveness probe."""

    async def test_health_returns_200(self, test_client: AsyncClient):
        response = await test_client.get("/api/health")
        assert response.status_code == 200

    async def test_health_contains_status_and_version(self, test_client: AsyncClient):
        response = await test_client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
        assert isinstance(data["version"], str)

    async def test_health_includes_service_name(self, test_client: AsyncClient):
        response = await test_client.get("/api/health")
        data = response.json()
        assert data.get("service") == "esportsforge"


class TestPlatformStatus:
    """GET /api/v1/status — backbone system state overview."""

    async def test_status_returns_200(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/status")
        assert response.status_code == 200

    async def test_status_contains_backbone_states(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/status")
        data = response.json()
        assert "backbone" in data
        backbone = data["backbone"]
        expected_keys = {
            "forge_data_fabric",
            "forge_core",
            "player_twin",
            "impact_rank",
            "truth_engine",
            "loop_ai",
        }
        assert expected_keys.issubset(set(backbone.keys()))

    async def test_status_contains_titles(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/status")
        data = response.json()
        assert "titles" in data
        assert "madden26" in data["titles"]

    async def test_status_platform_name(self, test_client: AsyncClient):
        response = await test_client.get("/api/v1/status")
        data = response.json()
        assert data.get("platform") == "EsportsForge"

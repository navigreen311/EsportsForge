import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    # Accept either — degraded means the DB probe failed, which depends on
    # which workflow is running (sqlite vs Postgres). Endpoint contract test.
    assert data["status"] in ("healthy", "degraded")
    assert data["service"] == "esportsforge"


@pytest.mark.asyncio
async def test_platform_status(client):
    response = await client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "EsportsForge"

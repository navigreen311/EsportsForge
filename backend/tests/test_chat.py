import pytest


@pytest.mark.asyncio
async def test_chat_endpoint(client):
    response = await client.post("/api/v1/chat", json={
        "message": "How do I beat cover 3?",
        "context": "dashboard"
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0


@pytest.mark.asyncio
async def test_chat_returns_actions(client):
    response = await client.post("/api/v1/chat", json={
        "message": "help with my gameplan",
        "context": "gameplan"
    })
    assert response.status_code == 200
    data = response.json()
    assert "actions" in data
    assert isinstance(data["actions"], list)

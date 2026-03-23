"""Tests for ClaudeClient — all Anthropic API calls are mocked."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai.claude_client import ClaudeClient, TokenUsage, _RateLimiter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _mock_response(text: str, input_tokens: int = 10, output_tokens: int = 20):
    """Build a fake Anthropic Message response."""
    resp = MagicMock()
    resp.content = [MagicMock(text=text)]
    resp.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    return resp


@pytest.fixture()
def client():
    """ClaudeClient with a mocked async Anthropic client."""
    with patch("app.services.ai.claude_client.anthropic.AsyncAnthropic") as mock_cls:
        instance = mock_cls.return_value
        instance.messages = MagicMock()
        instance.messages.create = AsyncMock()
        c = ClaudeClient(api_key="test-key", model="claude-test")
        yield c, instance


# ---------------------------------------------------------------------------
# TokenUsage
# ---------------------------------------------------------------------------

class TestTokenUsage:
    def test_record_and_summary(self):
        t = TokenUsage()
        t.record(100, 200, "model-a")
        t.record(50, 75, "model-b")

        assert t.total_input == 150
        assert t.total_output == 275
        assert t.total_tokens == 425
        assert t.call_count == 2

        s = t.summary()
        assert s["total_tokens"] == 425
        assert s["call_count"] == 2


# ---------------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------------

class TestRateLimiter:
    def test_allows_within_limit(self):
        rl = _RateLimiter(max_calls=3, period=60.0)
        rl.acquire()
        rl.acquire()
        rl.acquire()
        # 4th should raise
        with pytest.raises(Exception):
            rl.acquire()


# ---------------------------------------------------------------------------
# ClaudeClient.generate
# ---------------------------------------------------------------------------

class TestGenerate:
    @pytest.mark.asyncio
    async def test_generate_returns_text(self, client):
        c, mock_anthropic = client
        mock_anthropic.messages.create.return_value = _mock_response("Hello world")

        result = await c.generate("Say hello")
        assert result == "Hello world"
        assert c.usage.call_count == 1
        assert c.usage.total_input == 10
        assert c.usage.total_output == 20

    @pytest.mark.asyncio
    async def test_generate_passes_system_prompt(self, client):
        c, mock_anthropic = client
        mock_anthropic.messages.create.return_value = _mock_response("OK")

        await c.generate("test", system="You are helpful")
        call_kwargs = mock_anthropic.messages.create.call_args.kwargs
        assert call_kwargs["system"] == "You are helpful"

    @pytest.mark.asyncio
    async def test_generate_without_system(self, client):
        c, mock_anthropic = client
        mock_anthropic.messages.create.return_value = _mock_response("OK")

        await c.generate("test")
        call_kwargs = mock_anthropic.messages.create.call_args.kwargs
        assert "system" not in call_kwargs


# ---------------------------------------------------------------------------
# ClaudeClient.generate_json
# ---------------------------------------------------------------------------

class TestGenerateJson:
    @pytest.mark.asyncio
    async def test_parses_plain_json(self, client):
        c, mock_anthropic = client
        payload = {"recommendation": "Run the ball", "confidence": 0.8}
        mock_anthropic.messages.create.return_value = _mock_response(json.dumps(payload))

        result = await c.generate_json("test")
        assert result == payload

    @pytest.mark.asyncio
    async def test_strips_markdown_fences(self, client):
        c, mock_anthropic = client
        payload = {"answer": 42}
        wrapped = f"```json\n{json.dumps(payload)}\n```"
        mock_anthropic.messages.create.return_value = _mock_response(wrapped)

        result = await c.generate_json("test")
        assert result == payload

    @pytest.mark.asyncio
    async def test_invalid_json_raises(self, client):
        c, mock_anthropic = client
        mock_anthropic.messages.create.return_value = _mock_response("not json at all")

        with pytest.raises(json.JSONDecodeError):
            await c.generate_json("test")


# ---------------------------------------------------------------------------
# ClaudeClient.analyze
# ---------------------------------------------------------------------------

class TestAnalyze:
    @pytest.mark.asyncio
    async def test_analyze_returns_dict(self, client):
        c, mock_anthropic = client
        payload = {"analysis": "opponent favors passing", "confidence": 0.7}
        mock_anthropic.messages.create.return_value = _mock_response(json.dumps(payload))

        result = await c.analyze({"opponent": "Team A"}, "What is their tendency?")
        assert result["analysis"] == "opponent favors passing"


# ---------------------------------------------------------------------------
# ClaudeClient.decide
# ---------------------------------------------------------------------------

class TestDecide:
    @pytest.mark.asyncio
    async def test_decide_returns_dict(self, client):
        c, mock_anthropic = client
        payload = {
            "chosen": "Option A",
            "reasoning": "Best under pressure",
            "confidence": 0.9,
            "ranking": [
                {"option": "Option A", "score": 0.9},
                {"option": "Option B", "score": 0.6},
            ],
        }
        mock_anthropic.messages.create.return_value = _mock_response(json.dumps(payload))

        result = await c.decide(
            options=["Option A", "Option B"],
            context={"pressure": "high"},
            criteria="best under pressure",
        )
        assert result["chosen"] == "Option A"
        assert result["confidence"] == 0.9

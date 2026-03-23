"""Tests for Claude integration in Madden 26 intelligence agents.

Mocks the Claude client to verify prompt construction, response parsing,
and graceful fallback when the API is unavailable.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai.claude_client import ClaudeClient
from app.services.agents.madden26.scheme_ai import SchemeAI
from app.services.agents.madden26.gameplan_ai import GameplanAI
from app.services.agents.madden26.kill_sheet import KillSheetGenerator
from app.services.agents.madden26.read_ai import ReadAI
from app.services.agents.madden26.clock_ai import ClockAI
from app.services.agents.madden26.meta_bot import MetaBot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_claude_client(*, available: bool = True) -> ClaudeClient:
    """Return a mock ClaudeClient with controllable availability."""
    client = MagicMock(spec=ClaudeClient)
    client.is_available = available
    client.generate = AsyncMock(return_value="")
    client.generate_json = AsyncMock(return_value={})
    return client


# ===================================================================
# SchemeAI
# ===================================================================

class TestSchemeAIClaude:
    """SchemeAI Claude integration tests."""

    @pytest.mark.asyncio
    async def test_analyze_scheme_with_claude(self):
        """When Claude is available, analyze_scheme should call generate_json."""
        mock_response = {
            "description": "AI-generated spread analysis",
            "strengths": ["Speed", "Space creation"],
            "weaknesses": ["Weak run blocking"],
            "core_concepts": [
                {
                    "name": "Mesh",
                    "formation": "Gun Spread",
                    "primary_read": "Crossing route underneath",
                    "tags": ["quick", "man_beater"],
                    "beats_coverages": ["cover_1", "man_press"],
                    "down_distance_fit": ["3rd_and_short"],
                    "stackable_with": ["Flood"],
                }
            ],
            "best_formations": ["Gun Spread", "Gun Trips"],
            "recommended_playbooks": ["Bills", "Eagles"],
        }
        client = _make_claude_client(available=True)
        client.generate_json.return_value = mock_response

        scheme_ai = SchemeAI(claude_client=client)
        result = await scheme_ai.analyze_scheme("spread")

        client.generate_json.assert_awaited_once()
        assert result.scheme == "spread"
        assert result.description == "AI-generated spread analysis"
        assert len(result.core_concepts) == 1
        assert result.core_concepts[0].name == "Mesh"

    @pytest.mark.asyncio
    async def test_analyze_scheme_fallback_when_unavailable(self):
        """When Claude is unavailable, fall back to static data."""
        client = _make_claude_client(available=False)
        scheme_ai = SchemeAI(claude_client=client)

        result = await scheme_ai.analyze_scheme("west_coast")

        client.generate_json.assert_not_awaited()
        assert result.scheme == "west_coast"
        assert "West Coast" in result.description or "west" in result.description.lower()

    @pytest.mark.asyncio
    async def test_analyze_scheme_fallback_on_error(self):
        """When Claude raises an error, fall back gracefully."""
        client = _make_claude_client(available=True)
        client.generate_json.side_effect = RuntimeError("API error")

        scheme_ai = SchemeAI(claude_client=client)
        result = await scheme_ai.analyze_scheme("west_coast")

        # Should not raise — should return fallback data
        assert result.scheme == "west_coast"


# ===================================================================
# GameplanAI
# ===================================================================

class TestGameplanAIClaude:
    """GameplanAI Claude integration tests."""

    @pytest.mark.asyncio
    async def test_generate_gameplan_with_claude(self):
        """When Claude is available, generate_gameplan should use AI."""
        mock_response = {
            "plays": [
                {
                    "name": f"AI Play {i}",
                    "formation": "Gun Spread",
                    "play_type": "pass_short",
                    "concept": "Mesh",
                    "primary_read": "Crosser underneath",
                    "beats": ["cover_1"],
                    "situation_tags": ["3rd_and_short"],
                    "notes": "AI generated",
                }
                for i in range(10)
            ],
            "opening_script": [f"AI Play {i}" for i in range(5)],
            "gameplan_notes": "AI gameplan for spread offense.",
        }
        client = _make_claude_client(available=True)
        client.generate_json.return_value = mock_response

        gameplan_ai = GameplanAI(claude_client=client)
        result = await gameplan_ai.generate_gameplan(
            user_id=uuid.uuid4(),
            scheme="spread",
            meta_aware=False,
        )

        client.generate_json.assert_awaited_once()
        assert len(result.plays) == 10
        assert result.plays[0].name == "AI Play 0"

    @pytest.mark.asyncio
    async def test_generate_gameplan_fallback(self):
        """When Claude is unavailable, return template-based gameplan."""
        client = _make_claude_client(available=False)
        gameplan_ai = GameplanAI(claude_client=client)

        result = await gameplan_ai.generate_gameplan(
            user_id=uuid.uuid4(),
            meta_aware=False,
        )

        assert len(result.plays) == 10
        assert result.plays[0].name == "PA Boot Over"


# ===================================================================
# KillSheetGenerator
# ===================================================================

class TestKillSheetClaude:
    """KillSheetGenerator Claude integration tests."""

    @pytest.mark.asyncio
    async def test_generate_kill_sheet_ai_with_claude(self):
        """When Claude is available, generate_kill_sheet_ai should use AI."""
        from app.schemas.madden26.killsheet import OpponentData, Roster

        mock_response = {
            "kills": [
                {
                    "play_name": f"Kill {i}",
                    "playbook": "Gun Bunch",
                    "formation": "gun_bunch",
                    "concept": "mesh cross",
                    "effectiveness_score": 0.8,
                    "yards_per_attempt": 8.5,
                    "opponent_weakness_exploited": "high zone rate",
                    "hot_route_adjustments": ["Drag the TE"],
                    "setup_notes": "Motion RB left",
                }
                for i in range(5)
            ],
            "exploit_notes": ["Zone heavy"],
            "counter_warnings": ["Watch for man shift"],
        }
        client = _make_claude_client(available=True)
        client.generate_json.return_value = mock_response

        gen = KillSheetGenerator(claude_client=client)
        opponent = OpponentData(
            opponent_id="opp-123",
            opponent_name="TestOpponent",
            zone_coverage_rate=0.6,
            man_coverage_rate=0.3,
            blitz_rate=0.35,
        )
        roster = Roster(qb_overall=90, wr1_overall=88, rb_overall=85, oline_avg=82)

        result = await gen.generate_kill_sheet_ai("user-1", opponent, roster)

        client.generate_json.assert_awaited_once()
        assert len(result.kills) == 5
        assert result.kills[0].play_name == "Kill 0"

    @pytest.mark.asyncio
    async def test_generate_kill_sheet_fallback(self):
        """When Claude is unavailable, fall back to ranked static plays."""
        from app.schemas.madden26.killsheet import OpponentData, Roster

        client = _make_claude_client(available=False)
        gen = KillSheetGenerator(claude_client=client)
        opponent = OpponentData(
            opponent_id="opp-123",
            opponent_name="TestOpponent",
            zone_coverage_rate=0.6,
            man_coverage_rate=0.3,
            blitz_rate=0.35,
        )
        roster = Roster(qb_overall=90, wr1_overall=88, rb_overall=85, oline_avg=82)

        result = await gen.generate_kill_sheet_ai("user-1", opponent, roster)

        client.generate_json.assert_not_awaited()
        assert len(result.kills) == 5


# ===================================================================
# ReadAI
# ===================================================================

class TestReadAIClaude:
    """ReadAI Claude integration tests."""

    @pytest.mark.asyncio
    async def test_identify_coverage_ai_with_claude(self):
        """When Claude is available, identify_coverage_ai calls Claude."""
        mock_response = {
            "primary_coverage": "cover_2",
            "confidence": "high",
            "indicators": ["Two deep safeties split"],
            "vulnerable_zones": ["Deep middle"],
            "recommended_targets": ["Seam route"],
        }
        client = _make_claude_client(available=True)
        client.generate_json.return_value = mock_response

        read_ai = ReadAI(claude_client=client)
        result = await read_ai.identify_coverage_ai({
            "safety_count_deep": 2,
            "press": False,
        })

        client.generate_json.assert_awaited_once()
        assert result.primary_coverage.value == "cover_2"
        assert result.confidence.value == "high"

    @pytest.mark.asyncio
    async def test_identify_coverage_fallback(self):
        """When Claude is unavailable, use rule-based identification."""
        client = _make_claude_client(available=False)
        read_ai = ReadAI(claude_client=client)

        result = await read_ai.identify_coverage_ai({
            "safety_count_deep": 2,
            "press": False,
            "soft_coverage": True,
        })

        client.generate_json.assert_not_awaited()
        # Rule-based should identify Cover 4 with 2 deep + soft coverage
        assert result.primary_coverage.value == "cover_4"

    @pytest.mark.asyncio
    async def test_identify_blitz_ai_with_claude(self):
        """When Claude is available, identify_blitz_ai calls Claude."""
        mock_response = {
            "blitz_detected": True,
            "blitz_probability": 0.85,
            "likely_source": "mlb",
            "number_of_rushers": 6,
            "hot_route_suggestion": "Quick slant to the A-gap",
            "protection_adjustment": "Slide left",
            "indicators": ["MLB creeping to A-gap"],
        }
        client = _make_claude_client(available=True)
        client.generate_json.return_value = mock_response

        read_ai = ReadAI(claude_client=client)
        result = await read_ai.identify_blitz_ai({
            "defenders_near_los": 6,
            "blitz_indicators": ["MLB creeping to A-gap"],
        })

        assert result.blitz_detected is True
        assert result.blitz_probability == 0.85
        assert result.likely_source.value == "mlb"


# ===================================================================
# ClockAI
# ===================================================================

class TestClockAIClaude:
    """ClockAI Claude integration tests."""

    @pytest.mark.asyncio
    async def test_get_clock_decision_ai_with_claude(self):
        """When Claude is available, get_clock_decision_ai calls Claude."""
        from app.schemas.madden26.clock import GameState

        mock_response = {
            "action": "hurry_up",
            "reasoning": "Trailing in Q4 — must move fast.",
            "urgency": 0.9,
            "recommended_play_type": "pass_medium",
            "seconds_burned_estimate": 28.0,
        }
        client = _make_claude_client(available=True)
        client.generate_json.return_value = mock_response

        clock_ai = ClockAI(claude_client=client)
        game_state = GameState(
            quarter=4,
            time_remaining_seconds=90,
            score_user=17,
            score_opponent=24,
            down=2,
            yards_to_go=7,
            yard_line=35,
            is_user_possession=True,
            timeouts_user=2,
            timeouts_opponent=1,
        )

        result = await clock_ai.get_clock_decision_ai(game_state)

        client.generate_json.assert_awaited_once()
        assert result.action.value == "hurry_up"
        assert result.urgency == 0.9

    @pytest.mark.asyncio
    async def test_clock_decision_fallback(self):
        """When Claude is unavailable, use rule-based decision."""
        from app.schemas.madden26.clock import GameState

        client = _make_claude_client(available=False)
        clock_ai = ClockAI(claude_client=client)

        game_state = GameState(
            quarter=4,
            time_remaining_seconds=90,
            score_user=17,
            score_opponent=24,
            down=2,
            yards_to_go=7,
            yard_line=35,
            is_user_possession=True,
            timeouts_user=2,
            timeouts_opponent=1,
        )

        result = await clock_ai.get_clock_decision_ai(game_state)

        client.generate_json.assert_not_awaited()
        assert result.action.value == "hurry_up"


# ===================================================================
# MetaBot
# ===================================================================

class TestMetaBotClaude:
    """MetaBot Claude integration tests."""

    @pytest.mark.asyncio
    async def test_scan_weekly_meta_with_claude(self):
        """When Claude is available, scan_weekly_meta calls Claude."""
        mock_response = {
            "patch_version": "1.06",
            "top_strategies": ["Gun Bunch TE — AI-enhanced"],
            "rising_strategies": ["Tampa 2 AI variant"],
            "declining_strategies": ["Nano blitz"],
            "exploits": [
                {
                    "name": "AI Exploit",
                    "description": "AI-detected exploit",
                    "counter": "User the MLB",
                    "time_remaining": "1 week",
                    "risk_level": "high",
                }
            ],
            "meta_summary": "AI-generated meta analysis for patch 1.06.",
        }
        client = _make_claude_client(available=True)
        client.generate_json.return_value = mock_response

        meta_bot = MetaBot(claude_client=client)
        result = await meta_bot.scan_weekly_meta()

        client.generate_json.assert_awaited_once()
        assert result.meta_summary == "AI-generated meta analysis for patch 1.06."
        assert len(result.exploits) == 1

    @pytest.mark.asyncio
    async def test_scan_weekly_meta_fallback(self):
        """When Claude is unavailable, use static meta data."""
        client = _make_claude_client(available=False)
        meta_bot = MetaBot(claude_client=client)

        result = await meta_bot.scan_weekly_meta()

        client.generate_json.assert_not_awaited()
        assert "Gun Bunch" in result.meta_summary
        assert result.patch_version == "1.06"

    @pytest.mark.asyncio
    async def test_scan_weekly_meta_fallback_on_error(self):
        """When Claude raises an error, fall back gracefully."""
        client = _make_claude_client(available=True)
        client.generate_json.side_effect = RuntimeError("API down")

        meta_bot = MetaBot(claude_client=client)
        result = await meta_bot.scan_weekly_meta()

        assert result.patch_version == "1.06"


# ===================================================================
# ClaudeClient unit tests
# ===================================================================

class TestClaudeClient:
    """ClaudeClient availability and parsing tests."""

    def test_not_available_without_key(self):
        """Client reports unavailable with default placeholder key."""
        client = ClaudeClient(api_key="YOUR_ANTHROPIC_API_KEY_HERE")
        assert client.is_available is False

    def test_not_available_with_empty_key(self):
        """Client reports unavailable with empty key."""
        client = ClaudeClient(api_key="")
        assert client.is_available is False

    @pytest.mark.asyncio
    async def test_generate_raises_when_unavailable(self):
        """Calling generate when unavailable raises RuntimeError."""
        client = ClaudeClient(api_key="")
        with pytest.raises(RuntimeError, match="not available"):
            await client.generate("test prompt")

"""Tests for the LangGraph ForgeCore orchestrator — Claude calls are mocked."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai.langgraph_orchestrator import (
    ForgeOrchestrator,
    ForgeState,
    _agents_for_mode,
    _density_for_pressure,
    build_forge_graph,
    collect_data,
    deliver,
    filter_density,
    resolve_conflicts,
    run_agents,
)


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_density_for_pressure_critical(self):
        assert _density_for_pressure("critical") == "minimal"

    def test_density_for_pressure_medium(self):
        assert _density_for_pressure("medium") == "standard"

    def test_density_for_pressure_low(self):
        assert _density_for_pressure("low") == "detailed"

    def test_density_for_pressure_unknown(self):
        # invalid pressure defaults to "standard" via ValueError path
        assert _density_for_pressure("unknown") == "standard"

    def test_agents_for_ranked(self):
        agents = _agents_for_mode("ranked")
        assert "gameplan" in agents
        assert "scout" in agents

    def test_agents_for_tournament(self):
        agents = _agents_for_mode("tournament")
        # tournament skips gameplan
        assert "gameplan" not in agents
        assert "scout" in agents
        assert "impact_rank" in agents

    def test_agents_for_unknown_mode(self):
        agents = _agents_for_mode("nonexistent")
        assert agents == ["gameplan", "scout", "impact_rank", "player_twin"]


# ---------------------------------------------------------------------------
# Node: collect_data
# ---------------------------------------------------------------------------

class TestCollectData:
    @pytest.mark.asyncio
    async def test_sets_density_and_initializes(self):
        state: ForgeState = {
            "user_id": "u1",
            "title": "madden26",
            "context": {"pressure_state": "critical", "mode": "ranked"},
        }
        result = await collect_data(state)
        assert result["density"] == "minimal"
        assert result["agent_outputs"] == []
        assert result["conflicts"] == []
        assert result["error"] is None


# ---------------------------------------------------------------------------
# Node: filter_density
# ---------------------------------------------------------------------------

class TestFilterDensity:
    @pytest.mark.asyncio
    async def test_minimal_strips_reasoning(self):
        state: ForgeState = {
            "density": "minimal",
            "agent_outputs": [
                {"agent_name": "scout", "recommendation": "Blitz", "reasoning": "Long reason here."},
            ],
        }
        result = await filter_density(state)
        assert result["agent_outputs"][0]["reasoning"] == ""

    @pytest.mark.asyncio
    async def test_standard_keeps_first_sentence(self):
        state: ForgeState = {
            "density": "standard",
            "agent_outputs": [
                {
                    "agent_name": "scout",
                    "recommendation": "Blitz",
                    "reasoning": "First sentence. Second sentence. Third.",
                },
            ],
        }
        result = await filter_density(state)
        assert result["agent_outputs"][0]["reasoning"] == "First sentence."

    @pytest.mark.asyncio
    async def test_detailed_keeps_all(self):
        full_reasoning = "First. Second. Third."
        state: ForgeState = {
            "density": "detailed",
            "agent_outputs": [
                {"agent_name": "scout", "recommendation": "Blitz", "reasoning": full_reasoning},
            ],
        }
        result = await filter_density(state)
        assert result["agent_outputs"][0]["reasoning"] == full_reasoning


# ---------------------------------------------------------------------------
# Node: deliver (with mocked Claude)
# ---------------------------------------------------------------------------

class TestDeliver:
    @pytest.mark.asyncio
    async def test_empty_outputs_returns_fallback(self):
        state: ForgeState = {
            "agent_outputs": [],
            "context": {},
            "conflicts": [],
        }
        result = await deliver(state)
        decision = result["final_decision"]
        assert "No actionable" in decision["recommendation"]
        assert decision["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_deliver_calls_claude(self):
        mock_decision = {
            "recommendation": "Run slant routes",
            "reasoning": "Exploits weak secondary",
            "confidence": 0.85,
            "contributing_agents": ["scout", "gameplan"],
            "conflicts_resolved": [],
        }

        with patch("app.services.ai.langgraph_orchestrator.ClaudeClient") as MockClient:
            instance = MockClient.return_value
            instance.generate_json = AsyncMock(return_value=mock_decision)

            state: ForgeState = {
                "agent_outputs": [
                    {"agent_name": "scout", "recommendation": "Blitz", "confidence": 0.7, "reasoning": "R"},
                    {"agent_name": "gameplan", "recommendation": "Slant", "confidence": 0.8, "reasoning": "R"},
                ],
                "context": {"mode": "ranked"},
                "conflicts": [],
            }
            result = await deliver(state)

        assert result["final_decision"]["recommendation"] == "Run slant routes"
        assert result["final_decision"]["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_deliver_fallback_on_error(self):
        with patch("app.services.ai.langgraph_orchestrator.ClaudeClient") as MockClient:
            instance = MockClient.return_value
            instance.generate_json = AsyncMock(side_effect=Exception("API down"))

            state: ForgeState = {
                "agent_outputs": [
                    {"agent_name": "scout", "recommendation": "Blitz", "confidence": 0.7, "reasoning": "R"},
                    {"agent_name": "gameplan", "recommendation": "Slant", "confidence": 0.9, "reasoning": "R2"},
                ],
                "context": {"mode": "ranked"},
                "conflicts": [],
            }
            result = await deliver(state)

        # Should fallback to highest-confidence agent
        assert result["final_decision"]["recommendation"] == "Slant"
        assert result["final_decision"]["confidence"] == 0.9


# ---------------------------------------------------------------------------
# Node: run_agents (with mocked Claude)
# ---------------------------------------------------------------------------

class TestRunAgents:
    @pytest.mark.asyncio
    async def test_run_agents_calls_each(self):
        agent_response = {
            "recommendation": "Test rec",
            "confidence": 0.75,
            "reasoning": "Test reason",
            "data": {},
        }

        with patch("app.services.ai.langgraph_orchestrator.ClaudeClient") as MockClient:
            instance = MockClient.return_value
            instance.generate_json = AsyncMock(return_value=agent_response.copy())

            state: ForgeState = {
                "context": {"mode": "ranked", "pressure_state": "medium"},
                "agent_outputs": [],
            }
            result = await run_agents(state)

        # Should have called for each agent in ranked mode (4 agents)
        assert len(result["agent_outputs"]) == 4
        for output in result["agent_outputs"]:
            assert output["recommendation"] == "Test rec"
            assert "agent_name" in output

    @pytest.mark.asyncio
    async def test_run_agents_skips_on_error(self):
        call_count = 0

        async def _side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Agent failed")
            return {"recommendation": "OK", "confidence": 0.5, "reasoning": "", "data": {}}

        with patch("app.services.ai.langgraph_orchestrator.ClaudeClient") as MockClient:
            instance = MockClient.return_value
            instance.generate_json = AsyncMock(side_effect=_side_effect)

            state: ForgeState = {
                "context": {"mode": "ranked", "pressure_state": "medium"},
                "agent_outputs": [],
            }
            result = await run_agents(state)

        # 4 agents attempted, 1 failed, 3 succeeded
        assert len(result["agent_outputs"]) == 3


# ---------------------------------------------------------------------------
# Node: resolve_conflicts (with mocked Claude)
# ---------------------------------------------------------------------------

class TestResolveConflicts:
    @pytest.mark.asyncio
    async def test_skips_with_single_output(self):
        state: ForgeState = {
            "agent_outputs": [{"agent_name": "scout", "recommendation": "X"}],
        }
        result = await resolve_conflicts(state)
        assert result.get("conflicts", []) == [] or "conflicts" not in result

    @pytest.mark.asyncio
    async def test_detects_conflicts_via_claude(self):
        conflict_result = {
            "conflicts": [
                {
                    "conflicting_agents": ["scout", "gameplan"],
                    "description": "Scout says blitz, Gameplan says pass protect",
                }
            ]
        }

        with patch("app.services.ai.langgraph_orchestrator.ClaudeClient") as MockClient:
            instance = MockClient.return_value
            instance.generate_json = AsyncMock(return_value=conflict_result)

            state: ForgeState = {
                "agent_outputs": [
                    {"agent_name": "scout", "recommendation": "Blitz"},
                    {"agent_name": "gameplan", "recommendation": "Pass protect"},
                ],
            }
            result = await resolve_conflicts(state)

        assert len(result["conflicts"]) == 1
        assert "scout" in result["conflicts"][0]["conflicting_agents"]


# ---------------------------------------------------------------------------
# Full graph integration (with mocked Claude)
# ---------------------------------------------------------------------------

class TestForgeOrchestrator:
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        agent_resp = {
            "recommendation": "Counter the run",
            "confidence": 0.8,
            "reasoning": "Opponent runs 60% of plays.",
            "data": {},
        }
        conflict_resp = {"conflicts": []}
        forge_resp = {
            "recommendation": "Stack the box and blitz",
            "reasoning": "Opponent is run-heavy, blitz disrupts timing.",
            "confidence": 0.88,
            "contributing_agents": ["scout", "impact_rank"],
            "conflicts_resolved": [],
        }

        call_idx = 0

        async def _route_calls(*args, **kwargs):
            nonlocal call_idx
            call_idx += 1
            # First 4 calls = agent runs, 5th = conflict detection, 6th = deliver
            if call_idx <= 4:
                resp = agent_resp.copy()
                return resp
            if call_idx == 5:
                return conflict_resp
            return forge_resp

        with patch("app.services.ai.langgraph_orchestrator.ClaudeClient") as MockClient:
            instance = MockClient.return_value
            instance.generate_json = AsyncMock(side_effect=_route_calls)

            orchestrator = ForgeOrchestrator()
            result = await orchestrator.run(
                user_id="user-1",
                title="madden26",
                context={"mode": "ranked", "pressure_state": "medium"},
            )

        assert result["recommendation"] == "Stack the box and blitz"
        assert result["confidence"] == 0.88


# ---------------------------------------------------------------------------
# Graph structure
# ---------------------------------------------------------------------------

class TestGraphStructure:
    def test_graph_builds_without_error(self):
        graph = build_forge_graph()
        compiled = graph.compile()
        assert compiled is not None

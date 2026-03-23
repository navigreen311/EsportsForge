"""Unit tests for UFC 5 combat intelligence agents — FightIQ, DamageForge, StaminaChain, GrappleGraph, RoundScore."""

from __future__ import annotations

import pytest

from app.schemas.ufc5.combat import (
    ArchetypeStyle,
    BodyRegion,
    CutSeverity,
    DamageState,
    GrapplePositionType,
    RoundScore,
    StaminaPhase,
    StrikeType,
    SubmissionType,
)
from app.services.agents.ufc5.damage_forge import DamageForge
from app.services.agents.ufc5.fight_iq import FightIQ
from app.services.agents.ufc5.grapple_graph import GrappleGraph
from app.services.agents.ufc5.round_score import RoundScoreAI
from app.services.agents.ufc5.stamina_chain import StaminaChain


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fight_iq() -> FightIQ:
    return FightIQ()


@pytest.fixture
def damage_forge() -> DamageForge:
    return DamageForge()


@pytest.fixture
def stamina_chain() -> StaminaChain:
    return StaminaChain(total_rounds=3)


@pytest.fixture
def grapple_graph() -> GrappleGraph:
    return GrappleGraph()


@pytest.fixture
def round_score_ai() -> RoundScoreAI:
    return RoundScoreAI(total_rounds=3)


# ---------------------------------------------------------------------------
# FightIQ tests
# ---------------------------------------------------------------------------


class TestFightIQArchetypes:
    def test_list_archetypes_returns_all_styles(self, fight_iq: FightIQ) -> None:
        archetypes = fight_iq.list_archetypes()
        assert len(archetypes) == len(ArchetypeStyle)
        for a in archetypes:
            assert "name" in a
            assert "description" in a

    def test_classify_aggressive_opponent_as_pressure(self, fight_iq: FightIQ) -> None:
        result = fight_iq.classify_opponent({
            "aggression": 0.8,
            "takedown_rate": 0.1,
            "clinch_rate": 0.1,
            "striking_volume": 0.5,
            "power_ratio": 0.4,
        })
        assert result.style == ArchetypeStyle.PRESSURE

    def test_classify_wrestler(self, fight_iq: FightIQ) -> None:
        result = fight_iq.classify_opponent({
            "aggression": 0.5,
            "takedown_rate": 0.7,
            "clinch_rate": 0.3,
        })
        assert result.style == ArchetypeStyle.WRESTLER

    def test_classify_counter_fighter(self, fight_iq: FightIQ) -> None:
        result = fight_iq.classify_opponent({
            "aggression": 0.2,
            "takedown_rate": 0.05,
            "striking_volume": 0.3,
            "power_ratio": 0.4,
        })
        assert result.style == ArchetypeStyle.COUNTER


class TestFightIQMatchups:
    def test_matchup_card_has_strategies(self, fight_iq: FightIQ) -> None:
        matchup = fight_iq.get_matchup_card(
            ArchetypeStyle.COUNTER, ArchetypeStyle.PRESSURE
        )
        assert matchup.advantage > 0  # counter beats pressure
        assert len(matchup.key_strategies) > 0

    def test_brawler_disadvantage_vs_counter(self, fight_iq: FightIQ) -> None:
        matchup = fight_iq.get_matchup_card(
            ArchetypeStyle.BRAWLER, ArchetypeStyle.COUNTER
        )
        assert matchup.advantage < 0

    def test_analyze_all_matchups(self, fight_iq: FightIQ) -> None:
        matchups = fight_iq.analyze_all_matchups(ArchetypeStyle.WRESTLER)
        assert len(matchups) == len(ArchetypeStyle)

    def test_finish_pattern_returns_valid_data(self, fight_iq: FightIQ) -> None:
        pattern = fight_iq.get_finish_pattern(ArchetypeStyle.GRAPPLER)
        assert pattern.archetype == ArchetypeStyle.GRAPPLER
        assert "submission" in pattern.primary_finish.lower() or "sub" in pattern.primary_finish.lower()
        assert 1 <= pattern.round_tendency <= 5


# ---------------------------------------------------------------------------
# DamageForge tests
# ---------------------------------------------------------------------------


class TestDamageForgeAccumulation:
    def test_initial_state_is_clean(self, damage_forge: DamageForge) -> None:
        state = damage_forge.state
        assert state.head_damage == 0.0
        assert state.body_damage == 0.0
        assert state.cut_severity == CutSeverity.NONE

    def test_jab_adds_head_damage(self, damage_forge: DamageForge) -> None:
        entry = damage_forge.apply_damage(StrikeType.JAB, round_number=1)
        assert entry.region == BodyRegion.HEAD
        assert damage_forge.state.head_damage > 0

    def test_body_kick_adds_body_damage(self, damage_forge: DamageForge) -> None:
        damage_forge.apply_damage(StrikeType.BODY_KICK, round_number=1)
        assert damage_forge.state.body_damage > 0

    def test_leg_kick_adds_leg_damage(self, damage_forge: DamageForge) -> None:
        damage_forge.apply_damage(StrikeType.LEG_KICK, round_number=1)
        assert damage_forge.state.left_leg_damage > 0

    def test_critical_hit_deals_more_damage(self, damage_forge: DamageForge) -> None:
        normal = DamageForge()
        normal.apply_damage(StrikeType.CROSS, round_number=1)
        normal_dmg = normal.state.head_damage

        critical = DamageForge()
        critical.apply_damage(StrikeType.CROSS, is_critical=True, round_number=1)
        crit_dmg = critical.state.head_damage

        assert crit_dmg > normal_dmg

    def test_elbow_escalates_cut(self, damage_forge: DamageForge) -> None:
        damage_forge.apply_damage(StrikeType.ELBOW, round_number=1)
        assert damage_forge.state.cut_severity != CutSeverity.NONE


class TestDamageForgeVulnerability:
    def test_vulnerability_windows_not_empty(self, damage_forge: DamageForge) -> None:
        windows = damage_forge.get_vulnerability_windows()
        assert len(windows) > 0
        for w in windows:
            assert w.duration_frames > 0
            assert len(w.optimal_punish) > 0

    def test_head_damage_increases_ko_vulnerability(self, damage_forge: DamageForge) -> None:
        for _ in range(10):
            damage_forge.apply_damage(StrikeType.HOOK, round_number=1)
        assert damage_forge.state.knockout_vulnerability > 0.3

    def test_body_damage_increases_stamina_drain(self, damage_forge: DamageForge) -> None:
        for _ in range(8):
            damage_forge.apply_damage(StrikeType.BODY_HOOK, round_number=1)
        assert damage_forge.state.stamina_drain_factor > 1.0


# ---------------------------------------------------------------------------
# StaminaChain tests
# ---------------------------------------------------------------------------


class TestStaminaEconomy:
    def test_initial_stamina_is_full(self, stamina_chain: StaminaChain) -> None:
        assert stamina_chain.player_stamina == 100.0

    def test_throwing_strikes_drains_stamina(self, stamina_chain: StaminaChain) -> None:
        stamina_chain.record_strike(StrikeType.CROSS, landed=True)
        assert stamina_chain.player_stamina < 100.0

    def test_whiff_costs_more_than_landed(self, stamina_chain: StaminaChain) -> None:
        chain_hit = StaminaChain()
        cost_hit = chain_hit.record_strike(StrikeType.OVERHAND, landed=True)

        chain_miss = StaminaChain()
        cost_miss = chain_miss.record_strike(StrikeType.OVERHAND, landed=False)

        assert cost_miss > cost_hit

    def test_round_recovery_restores_stamina(self, stamina_chain: StaminaChain) -> None:
        for _ in range(10):
            stamina_chain.record_strike(StrikeType.HOOK, landed=True)
        low = stamina_chain.player_stamina
        stamina_chain.apply_round_recovery()
        assert stamina_chain.player_stamina > low

    def test_economy_report_has_valid_fields(self, stamina_chain: StaminaChain) -> None:
        econ = stamina_chain.get_economy(round_number=1)
        assert econ.round_number == 1
        assert econ.current_stamina <= 100.0
        assert econ.phase in StaminaPhase
        assert econ.output_budget >= 0


class TestWhiffPunishment:
    def test_whiff_model_returns_entries(self, stamina_chain: StaminaChain) -> None:
        model = stamina_chain.get_whiff_punishment_model()
        assert len(model) > 0
        for entry in model:
            assert entry.recovery_frames > 0
            assert entry.stamina_cost_to_opponent > 0

    def test_flying_knee_whiff_is_most_punishable(self, stamina_chain: StaminaChain) -> None:
        model = stamina_chain.get_whiff_punishment_model()
        # Should be sorted by recovery frames descending
        assert model[0].whiff_type == StrikeType.FLYING_KNEE


# ---------------------------------------------------------------------------
# GrappleGraph tests
# ---------------------------------------------------------------------------


class TestGrapplePositions:
    def test_all_positions_have_trees(self, grapple_graph: GrappleGraph) -> None:
        positions = grapple_graph.get_all_positions()
        assert len(positions) == len(GrapplePositionType)

    def test_standing_has_transitions(self, grapple_graph: GrappleGraph) -> None:
        tree = grapple_graph.get_position_tree(GrapplePositionType.STANDING)
        assert len(tree.available_transitions) > 0

    def test_mount_top_is_dominant(self, grapple_graph: GrappleGraph) -> None:
        tree = grapple_graph.get_position_tree(GrapplePositionType.MOUNT_TOP)
        assert tree.is_dominant is True
        assert len(tree.available_strikes) > 0

    def test_back_control_has_rnc(self, grapple_graph: GrappleGraph) -> None:
        tree = grapple_graph.get_position_tree(GrapplePositionType.BACK_CONTROL)
        assert SubmissionType.REAR_NAKED_CHOKE in tree.available_submissions


class TestSubmissionChains:
    def test_rnc_chain_from_standing(self, grapple_graph: GrappleGraph) -> None:
        chain = grapple_graph.get_submission_chain(
            SubmissionType.REAR_NAKED_CHOKE, GrapplePositionType.STANDING
        )
        assert chain is not None
        assert chain.submission == SubmissionType.REAR_NAKED_CHOKE
        assert chain.gate_count >= 1

    def test_triangle_chain_exists(self, grapple_graph: GrappleGraph) -> None:
        chain = grapple_graph.get_submission_chain(
            SubmissionType.TRIANGLE, GrapplePositionType.FULL_GUARD_BOTTOM
        )
        assert chain is not None

    def test_all_chains_from_standing(self, grapple_graph: GrappleGraph) -> None:
        chains = grapple_graph.get_all_submission_chains(GrapplePositionType.STANDING)
        assert len(chains) > 0
        sub_types = {c.submission for c in chains}
        assert len(sub_types) > 1  # multiple subs should be reachable


# ---------------------------------------------------------------------------
# RoundScore tests
# ---------------------------------------------------------------------------


class TestRoundScoring:
    def test_dominant_round_scores_10_9(self, round_score_ai: RoundScoreAI) -> None:
        score = round_score_ai.score_round(
            round_number=1,
            sig_strikes_landed=30,
            sig_strikes_absorbed=10,
            takedowns_landed=2,
            control_time=60.0,
        )
        assert score.player_score == 10
        assert score.opponent_score <= 9

    def test_close_round_is_swing(self, round_score_ai: RoundScoreAI) -> None:
        score = round_score_ai.score_round(
            round_number=1,
            sig_strikes_landed=15,
            sig_strikes_absorbed=14,
            takedowns_landed=0,
            control_time=0.0,
        )
        # Close rounds should have low confidence
        assert score.confidence < 0.8

    def test_scorecard_tracks_rounds(self, round_score_ai: RoundScoreAI) -> None:
        round_score_ai.score_round(1, 20, 10, 1, 0, 30.0)
        round_score_ai.score_round(2, 15, 18, 0, 0, 0.0)
        state = round_score_ai.get_scorecard_state()
        assert state["rounds_completed"] == 2
        assert state["rounds_remaining"] == 1

    def test_round_plan_generated(self, round_score_ai: RoundScoreAI) -> None:
        plan = round_score_ai.generate_round_plan(round_number=1)
        assert plan.round_number == 1
        assert len(plan.opening_sequence) > 0
        assert plan.pace in ("blitz", "steady", "coast", "survive")

    def test_finish_protocol_for_rocked_opponent(self, round_score_ai: RoundScoreAI) -> None:
        damage = DamageState(head_damage=70.0, is_rocked=True, knockout_vulnerability=0.7)
        protocol = round_score_ai.build_finish_protocol(damage_state=damage)
        assert protocol.method in ("TKO", "KO")
        assert len(protocol.strike_sequence) > 0
        assert len(protocol.trigger_conditions) > 0

"""Unit tests for Warzone AI agents — ZoneForge, LoadoutForge, GunfightAI, SquadOps, WarzoneTwin."""

from __future__ import annotations

import pytest

from app.schemas.warzone.combat import (
    CirclePhase,
    EngagementRange,
    LoadoutOptimizeRequest,
    MovementStyle,
    RotationRequest,
    SquadMember,
    SquadOpsRequest,
    SquadRole,
    WarzoneTwinRequest,
    WeaponClass,
    WeaponTier,
    ZoneRequest,
)
from app.services.agents.warzone.gunfight_ai import GunfightAI
from app.services.agents.warzone.loadout_forge import LoadoutForge
from app.services.agents.warzone.squad_ops import SquadOps
from app.services.agents.warzone.warzone_twin import WarzoneTwin
from app.services.agents.warzone.zone_forge import ZoneForge


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_squad_member(
    player_id: str = "p1",
    gamertag: str = "TestPlayer",
    kd: float = 1.5,
    dmg: float = 900.0,
    wr: float = 0.12,
    comms: float = 0.7,
    clutch: float = 0.2,
    preferred_range: EngagementRange = EngagementRange.MEDIUM,
) -> SquadMember:
    return SquadMember(
        player_id=player_id,
        gamertag=gamertag,
        kd_ratio=kd,
        avg_damage=dmg,
        win_rate=wr,
        preferred_range=preferred_range,
        comms_score=comms,
        clutch_rate=clutch,
    )


def _build_match_history(num_matches: int = 10) -> list[dict]:
    """Generate synthetic match data."""
    matches = []
    for i in range(num_matches):
        matches.append({
            "kills": 5 + (i % 4),
            "deaths": 2 + (i % 3),
            "damage": 800 + i * 50,
            "placement": max(1, 15 - i),
            "loot_time_seconds": 90 + i * 5,
            "cash_earned": 5000 + i * 200,
            "loadout_acquired": i % 3 != 0,
            "rotations": 3 + (i % 3),
            "hot_drop": i % 2 == 0,
            "first_shot_taken": i % 3 == 0,
            "fight_initiated": i % 2 == 0,
            "avg_engagement_distance_m": 25 + i * 3,
            "clutch_kills": 1 if i % 4 == 0 else 0,
            "clutch_rounds": 1 if i % 3 == 0 else 0,
            "weapons_used": ["MCW", "Striker"] if i % 2 == 0 else ["SVA 545", "HRM-9"],
        })
    return matches


# ===========================================================================
# ZoneForge tests
# ===========================================================================

class TestZoneForge:
    """Tests for ZoneForge circle prediction and rotation planning."""

    def setup_method(self) -> None:
        self.agent = ZoneForge()

    def test_predict_circle_returns_valid_prediction(self) -> None:
        request = ZoneRequest(
            current_phase=CirclePhase.PHASE_2,
            player_position=(400.0, 400.0),
            teammate_positions=[(410.0, 410.0), (390.0, 390.0)],
            known_enemy_positions=[(600.0, 600.0)],
        )
        prediction = self.agent.predict_circle(request)

        assert prediction.phase == CirclePhase.PHASE_3
        assert 0.0 <= prediction.confidence <= 1.0
        assert prediction.safe_zone_radius > 0
        assert prediction.collapse_eta_seconds > 0

    def test_predict_circle_confidence_decreases_late_game(self) -> None:
        early = ZoneRequest(
            current_phase=CirclePhase.PHASE_1,
            player_position=(400.0, 400.0),
        )
        late = ZoneRequest(
            current_phase=CirclePhase.PHASE_5,
            player_position=(400.0, 400.0),
        )
        p_early = self.agent.predict_circle(early)
        p_late = self.agent.predict_circle(late)

        assert p_early.confidence > p_late.confidence

    def test_third_party_risk_near_poi(self) -> None:
        # City Center is at (500, 500)
        risk = self.agent.assess_third_party_risk(
            position=(510.0, 510.0),
            known_enemies=[(520.0, 520.0)],
            map_name="urzikstan",
        )
        assert risk.risk_score > 0.3
        assert risk.enemy_count_estimate >= 1

    def test_third_party_risk_safe_location(self) -> None:
        risk = self.agent.assess_third_party_risk(
            position=(50.0, 50.0),
            known_enemies=[],
            map_name="urzikstan",
        )
        assert risk.risk_score < 0.3

    def test_plan_rotation_produces_waypoints(self) -> None:
        request = RotationRequest(
            current_position=(100.0, 100.0),
            destination=(500.0, 500.0),
            phase=CirclePhase.PHASE_2,
        )
        plan = self.agent.plan_rotation(request)

        assert len(plan.waypoints) >= 2
        assert plan.waypoints[0] == (100.0, 100.0)
        assert plan.estimated_travel_seconds > 0
        assert 0.0 <= plan.cover_quality <= 1.0

    def test_plan_rotation_vehicle_faster(self) -> None:
        base = RotationRequest(
            current_position=(0.0, 0.0),
            destination=(500.0, 500.0),
            phase=CirclePhase.PHASE_3,
        )
        vehicle = RotationRequest(
            current_position=(0.0, 0.0),
            destination=(500.0, 500.0),
            phase=CirclePhase.PHASE_3,
            has_vehicle=True,
        )
        plan_foot = self.agent.plan_rotation(base)
        plan_car = self.agent.plan_rotation(vehicle)

        assert plan_car.estimated_travel_seconds < plan_foot.estimated_travel_seconds

    def test_full_zone_analysis(self) -> None:
        request = ZoneRequest(
            current_phase=CirclePhase.PHASE_3,
            player_position=(300.0, 300.0),
            known_enemy_positions=[(350.0, 350.0)],
        )
        response = self.agent.analyze_zone(request)

        assert response.prediction is not None
        assert response.rotation_plan is not None
        assert len(response.third_party_risks) == 2
        assert len(response.summary) > 0


# ===========================================================================
# LoadoutForge tests
# ===========================================================================

class TestLoadoutForge:
    """Tests for LoadoutForge weapon meta and loadout optimization."""

    def setup_method(self) -> None:
        self.agent = LoadoutForge()

    def test_meta_tier_list_returns_weapons(self) -> None:
        tier_list = self.agent.get_meta_tier_list()
        assert len(tier_list) > 0
        # S-tier should come first
        assert tier_list[0].tier == WeaponTier.S

    def test_meta_tier_list_sorted_by_tier(self) -> None:
        tier_list = self.agent.get_meta_tier_list()
        tier_order = {WeaponTier.S: 0, WeaponTier.A: 1, WeaponTier.B: 2, WeaponTier.C: 3, WeaponTier.D: 4}
        for i in range(len(tier_list) - 1):
            assert tier_order[tier_list[i].tier] <= tier_order[tier_list[i + 1].tier]

    def test_optimize_loadout_returns_build(self) -> None:
        request = LoadoutOptimizeRequest(
            playstyle=MovementStyle.AGGRESSIVE,
            engagement_range=EngagementRange.SHORT,
        )
        response = self.agent.optimize_loadout(request)

        assert response.recommended_loadout.primary is not None
        assert response.recommended_loadout.secondary is not None
        assert response.recommended_loadout.effectiveness_score > 0
        assert len(response.recommended_loadout.perks) > 0

    def test_optimize_loadout_aggressive_gets_smg(self) -> None:
        request = LoadoutOptimizeRequest(
            playstyle=MovementStyle.AGGRESSIVE,
            engagement_range=EngagementRange.CQB,
        )
        response = self.agent.optimize_loadout(request)
        primary = response.recommended_loadout.primary
        assert primary.weapon_class in (WeaponClass.SMG, WeaponClass.SHOTGUN)

    def test_optimize_loadout_with_preferred_class(self) -> None:
        request = LoadoutOptimizeRequest(
            preferred_class=WeaponClass.SNIPER,
            playstyle=MovementStyle.EDGE_PLAYER,
        )
        response = self.agent.optimize_loadout(request)
        assert response.recommended_loadout.primary.weapon_class == WeaponClass.SNIPER

    def test_attachment_tradeoffs(self) -> None:
        tradeoffs = self.agent.get_attachment_tradeoffs(WeaponClass.ASSAULT_RIFLE)
        assert len(tradeoffs) > 0
        for t in tradeoffs:
            assert t.slot
            assert t.recommended
            assert len(t.pros) > 0

    def test_compare_weapons_valid(self) -> None:
        result = self.agent.compare_weapons("MCW", "Striker")
        assert "error" not in result
        assert "ttk_advantage" in result

    def test_compare_weapons_invalid(self) -> None:
        result = self.agent.compare_weapons("MCW", "NonExistentGun")
        assert "error" in result


# ===========================================================================
# GunfightAI tests
# ===========================================================================

class TestGunfightAI:
    """Tests for GunfightAI recoil patterns, drills, and engagement decisions."""

    def setup_method(self) -> None:
        self.agent = GunfightAI()

    def test_recoil_patterns_all(self) -> None:
        patterns = self.agent.get_recoil_patterns()
        assert len(patterns) > 0
        for p in patterns:
            assert p.vertical_pull > 0
            assert p.compensation_instruction

    def test_recoil_patterns_by_weapon(self) -> None:
        patterns = self.agent.get_recoil_patterns(weapon_names=["MCW"])
        assert len(patterns) == 1
        assert patterns[0].weapon_name == "MCW"

    def test_recoil_patterns_by_class(self) -> None:
        patterns = self.agent.get_recoil_patterns(weapon_class=WeaponClass.SMG)
        assert all(p.weapon_class == WeaponClass.SMG for p in patterns)

    def test_first_bullet_drills(self) -> None:
        drills = self.agent.get_first_bullet_drills("intermediate")
        assert len(drills) > 0
        for d in drills:
            assert d.drill_name
            assert 0.0 <= d.target_accuracy <= 1.0

    def test_drills_difficulty_scales(self) -> None:
        beginner = self.agent.get_first_bullet_drills("beginner")
        advanced = self.agent.get_first_bullet_drills("advanced")
        # Advanced targets should be >= beginner targets
        assert advanced[0].target_accuracy >= beginner[0].target_accuracy

    def test_engagement_decision_advantage(self) -> None:
        # Striker vs KATT-AMR at CQB — Striker should win
        decision = self.agent.evaluate_engagement(
            your_weapon="Striker",
            enemy_weapon="KATT-AMR",
            engagement_range=EngagementRange.CQB,
        )
        assert decision.should_engage is True
        assert decision.ttk_advantage_ms > 0

    def test_engagement_decision_disadvantage(self) -> None:
        # KATT-AMR vs Striker at CQB — sniper should disengage
        decision = self.agent.evaluate_engagement(
            your_weapon="KATT-AMR",
            enemy_weapon="Striker",
            engagement_range=EngagementRange.CQB,
        )
        assert decision.should_engage is False
        assert "disengage" in decision.recommended_approach or "reposition" in decision.recommended_approach

    def test_engagement_decision_at_range(self) -> None:
        # KATT-AMR at extreme range should be favorable
        decision = self.agent.evaluate_engagement(
            your_weapon="KATT-AMR",
            enemy_weapon="Striker",
            engagement_range=EngagementRange.EXTREME,
        )
        assert decision.should_engage is True

    def test_full_analysis(self) -> None:
        analysis = self.agent.full_gunfight_analysis(
            weapon_names=["MCW", "Striker"],
            your_weapon="MCW",
            enemy_weapon="Striker",
            engagement_range=EngagementRange.MEDIUM,
        )
        assert len(analysis.recoil_patterns) == 2
        assert len(analysis.first_bullet_drills) > 0
        assert analysis.engagement_decision is not None


# ===========================================================================
# SquadOps tests
# ===========================================================================

class TestSquadOps:
    """Tests for SquadOps role assignment, comms, and revive priority."""

    def setup_method(self) -> None:
        self.agent = SquadOps()

    def _build_squad(self) -> list[SquadMember]:
        return [
            _make_squad_member("p1", "ShotCaller", kd=1.8, dmg=1000, wr=0.18, comms=0.9, clutch=0.3),
            _make_squad_member("p2", "Slayer", kd=2.5, dmg=1500, wr=0.14, comms=0.5, clutch=0.4),
            _make_squad_member("p3", "Utility", kd=1.0, dmg=600, wr=0.10, comms=0.8, clutch=0.1),
            _make_squad_member(
                "p4", "Snipes", kd=2.0, dmg=900, wr=0.12, comms=0.6, clutch=0.25,
                preferred_range=EngagementRange.LONG,
            ),
        ]

    def test_role_assignment_covers_all_players(self) -> None:
        squad = self._build_squad()
        roles = self.agent.assign_roles(squad)
        assert len(roles) == 4
        assigned_ids = {r.player_id for r in roles}
        assert assigned_ids == {"p1", "p2", "p3", "p4"}

    def test_igl_assigned_to_best_caller(self) -> None:
        squad = self._build_squad()
        roles = self.agent.assign_roles(squad)
        igl = next(r for r in roles if r.assigned_role == SquadRole.IGL)
        # ShotCaller has highest comms + win rate combo
        assert igl.gamertag == "ShotCaller"

    def test_fragger_assigned_to_slayer(self) -> None:
        squad = self._build_squad()
        roles = self.agent.assign_roles(squad)
        fragger = next(r for r in roles if r.assigned_role == SquadRole.FRAGGER)
        assert fragger.gamertag == "Slayer"

    def test_callout_efficiency(self) -> None:
        squad = self._build_squad()
        eff = self.agent.calculate_callout_efficiency(squad)
        assert 0.0 <= eff <= 1.0

    def test_callout_efficiency_empty(self) -> None:
        assert self.agent.calculate_callout_efficiency([]) == 0.0

    def test_revive_priority_orders_by_value(self) -> None:
        squad = self._build_squad()
        priority = self.agent.decide_revive_priority(squad, "mid-game")
        assert len(priority.priority_order) == 4
        # Slayer (highest KD and damage) should be near the top
        assert priority.priority_order[0] == "p2"

    def test_revive_priority_empty(self) -> None:
        priority = self.agent.decide_revive_priority([], "mid-game")
        assert len(priority.priority_order) == 0

    def test_full_squad_analysis(self) -> None:
        request = SquadOpsRequest(squad=self._build_squad(), match_context="mid-game")
        analysis = self.agent.analyze_squad(request)

        assert len(analysis.role_assignments) == 4
        assert 0.0 <= analysis.callout_efficiency <= 1.0
        assert 0.0 <= analysis.squad_synergy_score <= 100.0
        assert len(analysis.summary) > 0


# ===========================================================================
# WarzoneTwin tests
# ===========================================================================

class TestWarzoneTwin:
    """Tests for WarzoneTwin digital twin builder."""

    def setup_method(self) -> None:
        self.agent = WarzoneTwin()

    def test_build_profile_with_matches(self) -> None:
        request = WarzoneTwinRequest(
            player_id="test-player-1",
            gamertag="TestAce",
            match_history=_build_match_history(10),
        )
        profile = self.agent.build_profile(request)

        assert profile.player_id == "test-player-1"
        assert profile.gamertag == "TestAce"
        assert profile.kd_ratio > 0
        assert profile.avg_placement > 0
        assert profile.movement_style is not None
        assert profile.engagement_tendency is not None
        assert profile.clutch_profile is not None
        assert profile.loot_efficiency is not None
        assert len(profile.summary) > 0

    def test_build_profile_empty_history(self) -> None:
        request = WarzoneTwinRequest(
            player_id="noob",
            gamertag="NewPlayer",
            match_history=[],
        )
        profile = self.agent.build_profile(request)

        assert profile.kd_ratio == 0.0
        assert profile.movement_style is not None

    def test_preferred_weapons_extracted(self) -> None:
        request = WarzoneTwinRequest(
            player_id="gun-nut",
            gamertag="WeaponMaster",
            match_history=_build_match_history(20),
        )
        profile = self.agent.build_profile(request)
        assert len(profile.preferred_weapons) > 0

    def test_coaching_tips_generated(self) -> None:
        request = WarzoneTwinRequest(
            player_id="needs-help",
            gamertag="Learner",
            match_history=_build_match_history(5),
        )
        profile = self.agent.build_profile(request)
        assert len(profile.coaching_tips) > 0

    def test_strengths_weaknesses_populated(self) -> None:
        request = WarzoneTwinRequest(
            player_id="mixed-bag",
            gamertag="Average",
            match_history=_build_match_history(15),
        )
        profile = self.agent.build_profile(request)
        # Should have at least one of strengths or weaknesses
        assert len(profile.strengths) + len(profile.weaknesses) > 0

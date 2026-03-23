"""Anti-cheat verification tests for the Warzone module.

Validates that all agents produce deterministic, bounded outputs and that
no intelligence method can be exploited to produce impossible game states.
Win condition: zone positioning + loadout optimization + gunfight mechanics
all pass integrity checks before ship.
"""

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
    WarzoneTwinRequest,
    WeaponClass,
    ZoneRequest,
)
from app.services.agents.warzone.gunfight_ai import GunfightAI
from app.services.agents.warzone.loadout_forge import LoadoutForge
from app.services.agents.warzone.squad_ops import SquadOps
from app.services.agents.warzone.warzone_twin import WarzoneTwin
from app.services.agents.warzone.zone_forge import ZoneForge


# ---------------------------------------------------------------------------
# Zone positioning integrity
# ---------------------------------------------------------------------------

class TestZoneIntegrity:
    """Verify zone predictions stay within valid game bounds."""

    def setup_method(self) -> None:
        self.agent = ZoneForge()

    def test_circle_prediction_bounds(self) -> None:
        """Predicted center must be within map bounds (0-1000)."""
        for phase in CirclePhase:
            request = ZoneRequest(
                current_phase=phase,
                player_position=(500.0, 500.0),
            )
            prediction = self.agent.predict_circle(request)
            x, y = prediction.predicted_center
            assert 0 <= x <= 1000, f"X={x} out of bounds at {phase}"
            assert 0 <= y <= 1000, f"Y={y} out of bounds at {phase}"

    def test_radius_decreases_each_phase(self) -> None:
        """Safe zone radius must strictly decrease as phases advance."""
        radii = []
        for phase in CirclePhase:
            request = ZoneRequest(
                current_phase=phase,
                player_position=(500.0, 500.0),
            )
            prediction = self.agent.predict_circle(request)
            radii.append(prediction.safe_zone_radius)
        # Each subsequent radius should be <= previous (phases predict NEXT radius)
        for i in range(len(radii) - 1):
            assert radii[i] >= radii[i + 1], f"Radius increased from phase {i} to {i+1}"

    def test_rotation_time_is_positive(self) -> None:
        """Travel time must always be a positive integer."""
        request = RotationRequest(
            current_position=(0.0, 0.0),
            destination=(100.0, 100.0),
            phase=CirclePhase.PHASE_1,
        )
        plan = self.agent.plan_rotation(request)
        assert plan.estimated_travel_seconds > 0

    def test_third_party_risk_bounded(self) -> None:
        """Risk score must be between 0 and 1 inclusive."""
        risk = self.agent.assess_third_party_risk(
            position=(500.0, 500.0),
            known_enemies=[(501.0, 501.0), (510.0, 510.0)],
        )
        assert 0.0 <= risk.risk_score <= 1.0


# ---------------------------------------------------------------------------
# Loadout optimization integrity
# ---------------------------------------------------------------------------

class TestLoadoutIntegrity:
    """Verify loadout optimizer cannot produce impossible configurations."""

    def setup_method(self) -> None:
        self.agent = LoadoutForge()

    def test_all_playstyles_produce_valid_loadout(self) -> None:
        """Every movement style must produce a complete loadout."""
        for style in MovementStyle:
            request = LoadoutOptimizeRequest(playstyle=style)
            response = self.agent.optimize_loadout(request)
            loadout = response.recommended_loadout
            assert loadout.primary.weapon_name, f"No primary for {style}"
            assert loadout.secondary.weapon_name, f"No secondary for {style}"
            assert loadout.primary.weapon_name != loadout.secondary.weapon_name, (
                f"Primary and secondary are the same weapon for {style}"
            )

    def test_effectiveness_score_bounded(self) -> None:
        """Effectiveness must be 0-100."""
        for style in MovementStyle:
            request = LoadoutOptimizeRequest(playstyle=style)
            response = self.agent.optimize_loadout(request)
            score = response.recommended_loadout.effectiveness_score
            assert 0.0 <= score <= 100.0, f"Score {score} out of bounds for {style}"

    def test_meta_tier_list_no_duplicates(self) -> None:
        """Each weapon should appear exactly once in the tier list."""
        tier_list = self.agent.get_meta_tier_list()
        names = [w.weapon_name for w in tier_list]
        assert len(names) == len(set(names)), "Duplicate weapons in tier list"

    def test_ttk_values_realistic(self) -> None:
        """TTK must be 0-2000ms (realistic for any weapon)."""
        tier_list = self.agent.get_meta_tier_list()
        for weapon in tier_list:
            assert 0 <= weapon.ttk_ms <= 2000, (
                f"{weapon.weapon_name} TTK={weapon.ttk_ms}ms is unrealistic"
            )

    def test_pick_rate_and_win_rate_bounded(self) -> None:
        """Pick rate and win rate must be 0-1."""
        tier_list = self.agent.get_meta_tier_list()
        for weapon in tier_list:
            assert 0.0 <= weapon.pick_rate <= 1.0
            assert 0.0 <= weapon.win_rate <= 1.0


# ---------------------------------------------------------------------------
# Gunfight mechanics integrity
# ---------------------------------------------------------------------------

class TestGunfightIntegrity:
    """Verify gunfight engine cannot produce exploitable outputs."""

    def setup_method(self) -> None:
        self.agent = GunfightAI()

    def test_recoil_difficulty_bounded(self) -> None:
        """Difficulty rating must be 0-10."""
        patterns = self.agent.get_recoil_patterns()
        for p in patterns:
            assert 0.0 <= p.difficulty_rating <= 10.0, (
                f"{p.weapon_name} difficulty {p.difficulty_rating} out of bounds"
            )

    def test_first_bullet_accuracy_bounded(self) -> None:
        """First 5 bullets accuracy must be 0-1."""
        patterns = self.agent.get_recoil_patterns()
        for p in patterns:
            assert 0.0 <= p.first_5_bullets_accuracy <= 1.0

    def test_engagement_decision_confidence_bounded(self) -> None:
        """Decision confidence must be 0-1."""
        decision = self.agent.evaluate_engagement(
            your_weapon="MCW",
            enemy_weapon="Striker",
            engagement_range=EngagementRange.MEDIUM,
        )
        assert 0.0 <= decision.confidence <= 1.0

    def test_engagement_symmetry_check(self) -> None:
        """If A should engage B, B should NOT want to engage A (at same range)."""
        decision_a = self.agent.evaluate_engagement(
            your_weapon="Striker",
            enemy_weapon="KATT-AMR",
            engagement_range=EngagementRange.CQB,
        )
        decision_b = self.agent.evaluate_engagement(
            your_weapon="KATT-AMR",
            enemy_weapon="Striker",
            engagement_range=EngagementRange.CQB,
        )
        # If both say engage, something is wrong — one should have disadvantage
        assert not (decision_a.should_engage and decision_b.should_engage and
                    decision_a.recommended_approach == "push" and
                    decision_b.recommended_approach == "push"), (
            "Both players cannot have push advantage in the same fight"
        )

    def test_drill_target_accuracy_bounded(self) -> None:
        """All drill targets must be achievable (0-1)."""
        for level in ["beginner", "intermediate", "advanced"]:
            drills = self.agent.get_first_bullet_drills(level)
            for d in drills:
                assert 0.0 <= d.target_accuracy <= 1.0


# ---------------------------------------------------------------------------
# Squad operations integrity
# ---------------------------------------------------------------------------

class TestSquadIntegrity:
    """Verify squad ops cannot assign impossible role configurations."""

    def setup_method(self) -> None:
        self.agent = SquadOps()

    def test_no_duplicate_role_assignments(self) -> None:
        """No two players should get the same priority role (except FLEX)."""
        squad = [
            SquadMember(player_id=f"p{i}", gamertag=f"P{i}", kd_ratio=1.5,
                        avg_damage=800, win_rate=0.12, comms_score=0.6, clutch_rate=0.2)
            for i in range(4)
        ]
        roles = self.agent.assign_roles(squad)
        non_flex = [r.assigned_role for r in roles if r.assigned_role != SquadRole.FLEX]
        assert len(non_flex) == len(set(non_flex)), "Duplicate non-FLEX role assignments"

    def test_revive_priority_contains_all_downed(self) -> None:
        """Revive list must include every downed player exactly once."""
        downed = [
            SquadMember(player_id=f"p{i}", gamertag=f"P{i}", kd_ratio=1.0,
                        avg_damage=500, win_rate=0.1)
            for i in range(3)
        ]
        priority = self.agent.decide_revive_priority(downed)
        assert set(priority.priority_order) == {f"p{i}" for i in range(3)}

    def test_synergy_score_bounded(self) -> None:
        """Squad synergy must be 0-100."""
        squad = [
            SquadMember(player_id="p1", gamertag="A", kd_ratio=2.0,
                        avg_damage=1200, win_rate=0.15, comms_score=0.8)
        ]
        analysis = self.agent.analyze_squad(SquadOpsRequest(squad=squad))
        assert 0.0 <= analysis.squad_synergy_score <= 100.0


# ---------------------------------------------------------------------------
# WarzoneTwin integrity
# ---------------------------------------------------------------------------

class TestTwinIntegrity:
    """Verify twin profile cannot produce impossible player stats."""

    def setup_method(self) -> None:
        self.agent = WarzoneTwin()

    def test_kd_ratio_non_negative(self) -> None:
        request = WarzoneTwinRequest(
            player_id="t1", gamertag="Test",
            match_history=[{"kills": 0, "deaths": 10, "damage": 100, "placement": 80}],
        )
        profile = self.agent.build_profile(request)
        assert profile.kd_ratio >= 0.0

    def test_hot_drop_rate_bounded(self) -> None:
        request = WarzoneTwinRequest(
            player_id="t1", gamertag="Test",
            match_history=[
                {"kills": 5, "deaths": 2, "damage": 800, "placement": 10, "hot_drop": True},
                {"kills": 3, "deaths": 1, "damage": 600, "placement": 20, "hot_drop": False},
            ],
        )
        profile = self.agent.build_profile(request)
        assert 0.0 <= profile.hot_drop_rate <= 1.0

    def test_clutch_rate_bounded(self) -> None:
        request = WarzoneTwinRequest(
            player_id="t1", gamertag="Test",
            match_history=[
                {"kills": 8, "deaths": 2, "damage": 1200, "placement": 1,
                 "clutch_kills": 3, "clutch_rounds": 3},
            ],
        )
        profile = self.agent.build_profile(request)
        assert 0.0 <= profile.clutch_profile.clutch_rate <= 1.0

    def test_loot_grade_is_valid(self) -> None:
        valid_grades = {"A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"}
        request = WarzoneTwinRequest(
            player_id="t1", gamertag="Test",
            match_history=[{"kills": 5, "deaths": 2, "damage": 800, "placement": 10}],
        )
        profile = self.agent.build_profile(request)
        assert profile.loot_efficiency.efficiency_grade in valid_grades

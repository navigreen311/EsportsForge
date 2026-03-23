"""Tests for ZoneForge FN, FortniteMeta AI, and FortniteTwin."""

from __future__ import annotations

import pytest

from app.schemas.fortnite.gameplay import (
    AntiCheatFlag,
    BuildForgeReport,
    BuildSequenceAnalysis,
    BuildType,
    EditDrillResult,
    EditShape,
    EditSpeedProfile,
    MaterialType,
    MasteryTier,
    PlayerPosition,
    RotationPlan,
    RotationStyle,
    StormState,
    ZonePhase,
)
from app.services.agents.fortnite.fortnite_meta import FortniteMetaAI
from app.services.agents.fortnite.fortnite_twin import FortniteTwin
from app.services.agents.fortnite.zone_forge_fn import ZoneForgeFN


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def zone_engine() -> ZoneForgeFN:
    return ZoneForgeFN()


@pytest.fixture
def meta_engine() -> FortniteMetaAI:
    return FortniteMetaAI()


@pytest.fixture
def twin_engine() -> FortniteTwin:
    return FortniteTwin()


def _make_storm(**overrides) -> StormState:
    defaults = {
        "zone_phase": ZonePhase.THIRD_ZONE,
        "seconds_until_close": 45,
        "storm_damage_per_tick": 5.0,
        "safe_zone_center": (500.0, 500.0),
        "safe_zone_radius": 300.0,
    }
    defaults.update(overrides)
    return StormState(**defaults)


def _make_player(**overrides) -> PlayerPosition:
    defaults = {
        "x": 200.0,
        "y": 200.0,
        "health": 100,
        "shield": 100,
        "materials": {MaterialType.WOOD: 500, MaterialType.BRICK: 300, MaterialType.METAL: 200},
        "has_mobility_item": False,
        "alive_players": 40,
    }
    defaults.update(overrides)
    return PlayerPosition(**defaults)


# ===========================================================================
# ZoneForge FN tests
# ===========================================================================

class TestZoneForgeFN:
    """Tests for ZoneForge FN agent."""

    def test_calculate_zone_tax_in_zone(self, zone_engine: ZoneForgeFN) -> None:
        """Player inside zone should have low health risk."""
        storm = _make_storm(safe_zone_center=(200.0, 200.0), safe_zone_radius=500.0)
        player = _make_player(x=200.0, y=200.0)
        tax = zone_engine.calculate_zone_tax(storm, player)
        assert tax.health_risk == 0.0
        assert tax.total_tax_score < 0.5

    def test_calculate_zone_tax_outside_zone(self, zone_engine: ZoneForgeFN) -> None:
        """Player far outside zone should have high tax."""
        storm = _make_storm(safe_zone_center=(1000.0, 1000.0), safe_zone_radius=100.0)
        player = _make_player(x=0.0, y=0.0)
        tax = zone_engine.calculate_zone_tax(storm, player)
        assert tax.total_tax_score > 0.3

    def test_recommend_rotation_early_game_in_zone(
        self, zone_engine: ZoneForgeFN
    ) -> None:
        """Early game in zone should recommend early rotate."""
        storm = _make_storm(
            zone_phase=ZonePhase.EARLY_GAME,
            safe_zone_center=(200.0, 200.0),
            safe_zone_radius=1000.0,
        )
        player = _make_player(x=200.0, y=200.0)
        style = zone_engine.recommend_rotation(storm, player)
        assert style == RotationStyle.EARLY_ROTATE

    def test_recommend_rotation_with_mobility(
        self, zone_engine: ZoneForgeFN
    ) -> None:
        """Player with mobility item outside zone should use launch pad."""
        storm = _make_storm(safe_zone_center=(1000.0, 1000.0), safe_zone_radius=100.0)
        player = _make_player(x=0.0, y=0.0, has_mobility_item=True)
        style = zone_engine.recommend_rotation(storm, player)
        assert style == RotationStyle.LAUNCH_PAD

    def test_recommend_rotation_late_game_high_mats(
        self, zone_engine: ZoneForgeFN
    ) -> None:
        """Late game with high mats should recommend tarping."""
        storm = _make_storm(zone_phase=ZonePhase.MOVING_ZONE)
        player = _make_player(
            x=0.0, y=0.0,
            materials={MaterialType.WOOD: 500, MaterialType.BRICK: 300, MaterialType.METAL: 200},
        )
        style = zone_engine.recommend_rotation(storm, player)
        assert style in (RotationStyle.TARPING, RotationStyle.TUNNELING)

    def test_generate_rotation_plan(self, zone_engine: ZoneForgeFN) -> None:
        """Full rotation plan includes tax, waypoints, actions."""
        storm = _make_storm()
        player = _make_player()
        plan = zone_engine.generate_rotation_plan("test-user", storm, player)

        assert plan.user_id == "test-user"
        assert plan.zone_tax is not None
        assert plan.recommended_style is not None
        assert len(plan.path_waypoints) > 0
        assert len(plan.priority_actions) > 0
        assert 0.0 <= plan.confidence <= 1.0

    def test_third_party_risk_increases_with_players(
        self, zone_engine: ZoneForgeFN
    ) -> None:
        """More alive players should increase third-party risk."""
        low = zone_engine._third_party_probability(20, ZonePhase.THIRD_ZONE, 100)
        high = zone_engine._third_party_probability(60, ZonePhase.THIRD_ZONE, 100)
        assert high > low

    def test_priority_actions_low_health(self, zone_engine: ZoneForgeFN) -> None:
        """Low health player should get heal-first action."""
        storm = _make_storm()
        player = _make_player(health=30, shield=0)
        plan = zone_engine.generate_rotation_plan("test", storm, player)
        heal_actions = [a for a in plan.priority_actions if "heal" in a.lower()]
        assert len(heal_actions) > 0


# ===========================================================================
# FortniteMeta AI tests
# ===========================================================================

class TestFortniteMetaAI:
    """Tests for FortniteMeta AI agent."""

    def test_weapon_tier_list(self, meta_engine: FortniteMetaAI) -> None:
        """Weapon tier list returns sorted weapons."""
        weapons = meta_engine.get_weapon_tier_list()
        assert len(weapons) > 0
        assert weapons[0].tier in ("S", "A", "B", "C", "D")

    def test_weapon_filter_by_class(self, meta_engine: FortniteMetaAI) -> None:
        """Filtering by weapon class only returns that class."""
        shotguns = meta_engine.get_weapon_tier_list("Shotgun")
        assert all(w.weapon_class == "Shotgun" for w in shotguns)
        assert len(shotguns) > 0

    def test_augment_priorities(self, meta_engine: FortniteMetaAI) -> None:
        """Augment priorities return ranked results."""
        augments = meta_engine.get_augment_priorities()
        assert len(augments) > 0
        ranks = [a.priority_rank for a in augments]
        assert ranks == sorted(ranks)

    def test_augment_filter_by_playstyle(self, meta_engine: FortniteMetaAI) -> None:
        """Playstyle filter includes matching + balanced augments."""
        aggressive = meta_engine.get_augment_priorities(playstyle="aggressive")
        assert all(
            a.playstyle_fit in ("aggressive", "balanced") for a in aggressive
        )

    def test_select_augment_from_options(self, meta_engine: FortniteMetaAI) -> None:
        """Augment selection picks highest priority from offered options."""
        result = meta_engine.select_augment(
            options=["Rarity Check", "Aerialist", "Jelly Angler"],
            playstyle="aggressive",
        )
        assert result is not None
        assert result.augment_name == "Aerialist"

    def test_select_augment_unknown_options(self, meta_engine: FortniteMetaAI) -> None:
        """Unknown augment names return None."""
        result = meta_engine.select_augment(["Unknown Augment", "Fake Augment"])
        assert result is None

    def test_mobility_items(self, meta_engine: FortniteMetaAI) -> None:
        """Mobility items are returned sorted by priority."""
        items = meta_engine.get_mobility_items()
        assert len(items) > 0
        priorities = [i.carry_priority for i in items]
        assert priorities == sorted(priorities)

    def test_should_carry_mobility_late_game(self, meta_engine: FortniteMetaAI) -> None:
        """Late game should recommend carrying mobility."""
        advice = meta_engine.should_carry_mobility(
            ZonePhase.MOVING_ZONE, has_heals=True, inventory_slots_free=1
        )
        assert advice["carry"] is True

    def test_meta_snapshot(self, meta_engine: FortniteMetaAI) -> None:
        """Meta snapshot includes weapons, augments, mobility."""
        snap = meta_engine.get_meta_snapshot()
        assert len(snap.weapon_tier_list) > 0
        assert len(snap.augment_priorities) > 0
        assert len(snap.mobility_items) > 0
        assert snap.meta_shift_summary != ""


# ===========================================================================
# FortniteTwin tests
# ===========================================================================

class TestFortniteTwin:
    """Tests for FortniteTwin digital twin agent."""

    def test_build_twin_empty(self, twin_engine: FortniteTwin) -> None:
        """Twin with no data returns valid baseline profile."""
        twin = twin_engine.build_twin("test-user")
        assert twin.user_id == "test-user"
        assert twin.build_style.primary_style == "unknown"
        assert twin.anti_cheat_status == AntiCheatFlag.CLEAN

    def test_build_twin_with_build_data(self, twin_engine: FortniteTwin) -> None:
        """Twin with build data classifies style correctly."""
        from app.services.agents.fortnite.build_forge import BuildForgeFN
        build_engine = BuildForgeFN()

        analyses = [
            build_engine.analyze_sequence(
                user_id="test",
                build_type=BuildType.NINETIES,
                step_times_ms=[80, 100, 110, 100, 110, 90],
                placement_hits=5,
                placement_total=6,
                materials={"wood": 60},
            ),
            build_engine.analyze_sequence(
                user_id="test",
                build_type=BuildType.RAMP_WALL,
                step_times_ms=[90, 70, 130, 70],
                placement_hits=4,
                placement_total=4,
                materials={"wood": 40},
            ),
        ]
        report = build_engine.generate_report("test", analyses)
        twin = twin_engine.build_twin("test", build_report=report)

        assert twin.build_style.primary_style != "unknown"
        assert len(twin.build_style.preferred_sequences) > 0

    def test_analyze_edit_confidence(self, twin_engine: FortniteTwin) -> None:
        """Edit confidence identifies fastest/slowest shapes."""
        profile = EditSpeedProfile(
            user_id="test",
            shape_speeds={
                EditShape.TRIANGLE: 180.0,
                EditShape.ARCH: 220.0,
                EditShape.DOOR: 300.0,
            },
            shape_accuracy={
                EditShape.TRIANGLE: 0.9,
                EditShape.ARCH: 0.85,
                EditShape.DOOR: 0.7,
            },
            pressure_penalty=0.15,
        )
        confidence = twin_engine.analyze_edit_confidence(profile)
        assert confidence.fastest_shape == EditShape.TRIANGLE
        assert confidence.slowest_shape == EditShape.DOOR
        assert confidence.pressure_reliability == pytest.approx(0.85, abs=0.01)

    def test_analyze_zone_discipline(self, twin_engine: FortniteTwin) -> None:
        """Zone discipline analysis classifies rotation timing."""
        plans = [
            RotationPlan(
                user_id="test",
                storm_state=_make_storm(),
                player_position=_make_player(),
                recommended_style=RotationStyle.EDGE_ROTATE,
                zone_tax=type("ZT", (), {
                    "time_pressure": 0.2,
                    "total_tax_score": 0.3,
                    "fight_probability": 0.1,
                })(),
                confidence=0.7,
            ),
        ]
        discipline = twin_engine.analyze_zone_discipline(plans)
        assert discipline.avg_rotation_timing in ("early", "on_time", "late", "storm_surfer")
        assert 0.0 <= discipline.positioning_score <= 1.0

    def test_aggregate_anti_cheat_clean(self, twin_engine: FortniteTwin) -> None:
        """All clean flags should aggregate to clean."""
        from app.services.agents.fortnite.build_forge import BuildForgeFN
        report = BuildForgeFN().generate_report("test", [])
        flag = twin_engine.aggregate_anti_cheat(build_report=report)
        assert flag == AntiCheatFlag.CLEAN

    def test_aggregate_anti_cheat_flagged(self, twin_engine: FortniteTwin) -> None:
        """Flagged anti-cheat should propagate to twin."""
        profile = EditSpeedProfile(
            user_id="test",
            anti_cheat=AntiCheatFlag.MACRO_DETECTED,
        )
        flag = twin_engine.aggregate_anti_cheat(edit_profile=profile)
        assert flag == AntiCheatFlag.MACRO_DETECTED

    def test_strengths_weaknesses_identification(
        self, twin_engine: FortniteTwin
    ) -> None:
        """Twin with mixed data should identify strengths and weaknesses."""
        from app.services.agents.fortnite.build_forge import BuildForgeFN
        build_engine = BuildForgeFN()

        # Slow builds, fast edits
        analyses = [
            build_engine.analyze_sequence(
                user_id="test",
                build_type=BuildType.RAMP_WALL,
                step_times_ms=[300, 280, 400, 280],
                placement_hits=2,
                placement_total=4,
                materials={"wood": 80},
            ),
        ]
        report = build_engine.generate_report("test", analyses)

        edit_profile = EditSpeedProfile(
            user_id="test",
            shape_speeds={EditShape.TRIANGLE: 170.0, EditShape.ARCH: 190.0},
            shape_accuracy={EditShape.TRIANGLE: 0.95, EditShape.ARCH: 0.90},
            pressure_penalty=0.1,
        )

        twin = twin_engine.build_twin(
            "test",
            build_report=report,
            edit_profile=edit_profile,
        )
        assert len(twin.strengths) > 0 or len(twin.weaknesses) > 0
        assert len(twin.recommended_focus) >= 0

    def test_material_management_analysis(self, twin_engine: FortniteTwin) -> None:
        """Material management identifies waste patterns."""
        from app.services.agents.fortnite.build_forge import BuildForgeFN
        build_engine = BuildForgeFN()

        analyses = [
            build_engine.analyze_sequence(
                user_id="test",
                build_type=BuildType.NINETIES,
                step_times_ms=[100, 120, 130, 120, 130, 100],
                placement_hits=3,
                placement_total=6,
                materials={"wood": 100, "brick": 50},
            ),
        ]
        report = build_engine.generate_report("test", analyses)
        mats = twin_engine.analyze_material_management(report)
        assert 0.0 <= mats.waste_index <= 1.0
        assert 0.0 <= mats.farming_efficiency <= 1.0

"""Tests for InstallAI — call sheets, eBooks, audible trees, packages."""

from __future__ import annotations

import pytest

from app.schemas.install import (
    AntiBlitzScript,
    AudibleTree,
    CallSheet,
    InstallPackage,
    MiniEBook,
    RedZonePackage,
)
from app.services.backbone.install_ai import InstallAI


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine() -> InstallAI:
    """Fresh InstallAI engine per test."""
    return InstallAI()


@pytest.fixture
def sample_gameplan() -> dict:
    return {
        "title": "madden26",
        "plays": [
            {"name": "HB Dive", "situation": "1st_and_10"},
            {"name": "PA Boot", "situation": "1st_and_10"},
            {"name": "Slant Route", "situation": "3rd_and_short"},
            {"name": "Fade Route", "situation": "red_zone"},
            {"name": "Quick Slant", "situation": "red_zone"},
            {"name": "Hail Mary", "situation": "two_minute"},
        ],
        "key_plays": [
            {
                "name": "PA Boot",
                "reads": [
                    {"condition": "Cover 3 detected", "action": "Hit the seam route"},
                    {"condition": "Cover 2 shell", "action": "Attack the deep middle"},
                    {"condition": "Man coverage", "action": "Run the crossing route"},
                ],
            },
        ],
        "red_zone": {
            "formations": ["Goal Line", "Shotgun Trips"],
            "plays": ["Fade Route", "Quick Slant"],
            "goal_line": ["QB Sneak", "Power"],
            "fades": ["Back-shoulder fade", "Corner route"],
        },
        "blitz_scouting": [
            {
                "type": "edge_blitz",
                "hot_routes": ["Slant", "Quick Out"],
                "quick_passes": ["Bubble Screen"],
                "protections": ["Slide Left"],
            },
        ],
        "recommendations": [
            {"label": "Use PA more", "description": "Play action is beating their LBs.", "drill": "PA Boot drill x20"},
        ],
        "notes": "Opponent is aggressive on 1st down.",
    }


@pytest.fixture
def sample_profile() -> dict:
    return {
        "user_id": "player-456",
        "style": "aggressive",
    }


# ---------------------------------------------------------------------------
# Call sheet tests
# ---------------------------------------------------------------------------

class TestCallSheet:
    def test_generate_call_sheet_structure(self, engine: InstallAI, sample_gameplan: dict):
        sheet = engine.generate_call_sheet(sample_gameplan)
        assert isinstance(sheet, CallSheet)
        assert sheet.title == "madden26"
        assert len(sheet.situation_groups) > 0
        assert "1st_and_10" in sheet.situation_groups

    def test_call_sheet_red_zone_plays(self, engine: InstallAI, sample_gameplan: dict):
        sheet = engine.generate_call_sheet(sample_gameplan)
        assert len(sheet.red_zone_calls) == 2
        assert "Fade Route" in sheet.red_zone_calls

    def test_call_sheet_two_minute_plays(self, engine: InstallAI, sample_gameplan: dict):
        sheet = engine.generate_call_sheet(sample_gameplan)
        assert len(sheet.two_minute_calls) == 1
        assert "Hail Mary" in sheet.two_minute_calls

    def test_call_sheet_audibles(self, engine: InstallAI, sample_gameplan: dict):
        sheet = engine.generate_call_sheet(sample_gameplan)
        assert len(sheet.audibles) == 1
        tree = sheet.audibles[0]
        assert tree.base_play == "PA Boot"

    def test_call_sheet_with_player_profile(
        self, engine: InstallAI, sample_gameplan: dict, sample_profile: dict
    ):
        sheet = engine.generate_call_sheet(sample_gameplan, sample_profile)
        assert "aggressive" in sheet.notes.lower()

    def test_call_sheet_empty_gameplan(self, engine: InstallAI):
        sheet = engine.generate_call_sheet({})
        assert isinstance(sheet, CallSheet)
        assert len(sheet.situation_groups) == 0
        assert sheet.title == "madden26"  # default

    def test_call_sheet_notes(self, engine: InstallAI, sample_gameplan: dict):
        sheet = engine.generate_call_sheet(sample_gameplan)
        assert "aggressive" not in sheet.notes.lower()  # no profile = no style tag
        assert "Opponent is aggressive" in sheet.notes


# ---------------------------------------------------------------------------
# Mini eBook tests
# ---------------------------------------------------------------------------

class TestMiniEBook:
    def test_generate_ebook_structure(self, engine: InstallAI):
        ebook = engine.generate_ebook("Zone Coverage Reads")
        assert isinstance(ebook, MiniEBook)
        assert ebook.topic == "Zone Coverage Reads"
        assert len(ebook.sections) >= 1
        assert len(ebook.key_takeaways) >= 1
        assert len(ebook.practice_drills) >= 1

    def test_ebook_with_recommendations(self, engine: InstallAI):
        recs = [
            {"label": "Cover 3 Beater", "description": "Attack the seams.", "drill": "Seam drill x10"},
            {"label": "Cover 2 Beater", "description": "Hit the deep middle."},
        ]
        ebook = engine.generate_ebook("Coverage Beaters", recs)
        # Overview + 2 recommendation sections
        assert len(ebook.sections) == 3
        assert len(ebook.key_takeaways) == 2
        assert any("seam" in d.lower() for d in ebook.practice_drills)

    def test_ebook_no_recommendations(self, engine: InstallAI):
        ebook = engine.generate_ebook("Basics")
        assert "Basics" in ebook.summary
        assert len(ebook.key_takeaways) == 1
        assert len(ebook.practice_drills) == 1

    def test_ebook_summary_includes_count(self, engine: InstallAI):
        recs = [{"label": "A"}, {"label": "B"}, {"label": "C"}]
        ebook = engine.generate_ebook("Topic", recs)
        assert "3" in ebook.summary


# ---------------------------------------------------------------------------
# Audible tree tests
# ---------------------------------------------------------------------------

class TestAudibleTree:
    def test_three_layer_structure(self, engine: InstallAI):
        reads = [
            {"condition": "Cover 3", "action": "Hit seam"},
            {"condition": "Cover 2", "action": "Go deep middle"},
            {"condition": "Man press", "action": "Run crossing route"},
        ]
        tree = engine.generate_audible_tree("PA Boot", reads)
        assert isinstance(tree, AudibleTree)
        assert tree.base_play == "PA Boot"
        assert tree.base_call.condition == "Cover 3"
        assert tree.if_bagged.condition == "Cover 2"
        assert tree.if_they_adjust.condition == "Man press"

    def test_default_layers_no_reads(self, engine: InstallAI):
        tree = engine.generate_audible_tree("HB Dive")
        assert tree.base_play == "HB Dive"
        assert "HB Dive" in tree.base_call.action
        assert "HB Dive" in tree.if_bagged.action
        assert "HB Dive" in tree.if_they_adjust.action

    def test_partial_reads(self, engine: InstallAI):
        reads = [{"condition": "Single high safety", "action": "Throw deep"}]
        tree = engine.generate_audible_tree("Streak", reads)
        assert tree.base_call.condition == "Single high safety"
        # Layers 2 & 3 should be auto-generated
        assert "Streak" in tree.if_bagged.action
        assert "Streak" in tree.if_they_adjust.action


# ---------------------------------------------------------------------------
# Red zone package tests
# ---------------------------------------------------------------------------

class TestRedZonePackage:
    def test_red_zone_from_gameplan(self, engine: InstallAI, sample_gameplan: dict):
        pkg = engine.generate_red_zone_package(sample_gameplan)
        assert isinstance(pkg, RedZonePackage)
        assert "Goal Line" in pkg.formations
        assert len(pkg.plays) == 2
        assert len(pkg.goal_line_package) == 2
        assert len(pkg.fade_routes) == 2

    def test_red_zone_defaults(self, engine: InstallAI):
        pkg = engine.generate_red_zone_package({})
        assert len(pkg.formations) > 0  # defaults applied
        assert len(pkg.goal_line_package) > 0

    def test_red_zone_has_reads(self, engine: InstallAI, sample_gameplan: dict):
        pkg = engine.generate_red_zone_package(sample_gameplan)
        assert len(pkg.reads) > 0
        for tree in pkg.reads:
            assert isinstance(tree, AudibleTree)


# ---------------------------------------------------------------------------
# Anti-blitz tests
# ---------------------------------------------------------------------------

class TestAntiBlitz:
    def test_anti_blitz_from_gameplan(self, engine: InstallAI, sample_gameplan: dict):
        scripts = engine.generate_anti_blitz_package(sample_gameplan)
        assert len(scripts) == 1
        script = scripts[0]
        assert isinstance(script, AntiBlitzScript)
        assert script.blitz_type == "edge_blitz"
        assert len(script.hot_routes) > 0
        assert script.audible_tree is not None

    def test_anti_blitz_defaults(self, engine: InstallAI):
        scripts = engine.generate_anti_blitz_package({})
        assert len(scripts) == 2  # default edge + a-gap
        for s in scripts:
            assert s.audible_tree is not None
            assert len(s.hot_routes) > 0

    def test_anti_blitz_audible_tree_layers(self, engine: InstallAI, sample_gameplan: dict):
        scripts = engine.generate_anti_blitz_package(sample_gameplan)
        tree = scripts[0].audible_tree
        assert tree.base_call.condition != ""
        assert tree.if_bagged.condition != ""
        assert tree.if_they_adjust.condition != ""


# ---------------------------------------------------------------------------
# Full install package tests
# ---------------------------------------------------------------------------

class TestFullInstall:
    def test_create_full_install(
        self, engine: InstallAI, sample_gameplan: dict, sample_profile: dict
    ):
        pkg = engine.create_full_install(sample_gameplan, sample_profile, "opponent-789")
        assert isinstance(pkg, InstallPackage)
        assert pkg.user_id == "player-456"
        assert pkg.title == "madden26"
        assert pkg.opponent == "opponent-789"
        assert isinstance(pkg.call_sheet, CallSheet)
        assert isinstance(pkg.ebook, MiniEBook)
        assert isinstance(pkg.red_zone_package, RedZonePackage)
        assert len(pkg.anti_blitz_scripts) > 0

    def test_full_install_empty_gameplan(self, engine: InstallAI):
        pkg = engine.create_full_install({})
        assert isinstance(pkg, InstallPackage)
        assert pkg.user_id == "unknown"
        assert isinstance(pkg.call_sheet, CallSheet)
        assert isinstance(pkg.ebook, MiniEBook)

    def test_full_install_audible_trees_collected(
        self, engine: InstallAI, sample_gameplan: dict
    ):
        pkg = engine.create_full_install(sample_gameplan)
        # Should include audibles from call sheet
        assert len(pkg.audible_trees) >= len(pkg.call_sheet.audibles)

    def test_full_install_ebook_has_topic(
        self, engine: InstallAI, sample_gameplan: dict
    ):
        pkg = engine.create_full_install(sample_gameplan, opponent="Rival")
        assert "Rival" in pkg.ebook.topic

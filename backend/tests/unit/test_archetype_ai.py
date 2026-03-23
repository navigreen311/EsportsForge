"""Unit tests for ArchetypeAI — opponent archetype classification."""

from __future__ import annotations

import pytest

from app.schemas.opponent import Archetype, ArchetypeLabel, CounterPackage
from app.services.backbone.archetype_ai import (
    classify_opponent,
    get_archetype_library,
    get_counter_package,
    update_mid_game,
)


# ---------------------------------------------------------------------------
# classify_opponent
# ---------------------------------------------------------------------------

class TestClassifyOpponent:
    def test_returns_unknown_with_no_signals(self):
        result = classify_opponent({"signals": [], "title": "madden26"})

        assert isinstance(result, Archetype)
        assert result.label == ArchetypeLabel.UNKNOWN
        assert result.confidence == 0.0

    def test_classifies_aggressor(self):
        signals = ["high tempo", "risk-taking", "blitz-heavy"]
        result = classify_opponent({"signals": signals, "title": "madden26"})

        assert result.label == ArchetypeLabel.AGGRESSOR
        assert result.confidence > 0.0

    def test_classifies_turtle(self):
        signals = ["conservative", "clock-management", "run-heavy"]
        result = classify_opponent({"signals": signals, "title": "cfb26"})

        assert result.label == ArchetypeLabel.TURTLE
        assert result.confidence > 0.0

    def test_classifies_chaos_agent(self):
        signals = ["unpredictable", "trick-plays", "no-huddle"]
        result = classify_opponent({"signals": signals, "title": "madden26"})

        assert result.label == ArchetypeLabel.CHAOS_AGENT

    def test_classifies_meta_slave(self):
        signals = ["meta-optimal", "scheme-heavy", "community-plays"]
        result = classify_opponent({"signals": signals, "title": "madden26"})

        assert result.label == ArchetypeLabel.META_SLAVE

    def test_classifies_one_trick(self):
        signals = ["repetitive", "one-scheme", "comfort-zone"]
        result = classify_opponent({"signals": signals, "title": "madden26"})

        assert result.label == ArchetypeLabel.ONE_TRICK

    def test_weak_signals_return_unknown(self):
        signals = ["some-random-trait"]
        result = classify_opponent({"signals": signals, "title": "madden26"})

        assert result.label == ArchetypeLabel.UNKNOWN

    def test_includes_title_in_result(self):
        signals = ["high tempo", "blitz-heavy"]
        result = classify_opponent({"signals": signals, "title": "cfb26"})

        assert result.title == "cfb26"


# ---------------------------------------------------------------------------
# get_counter_package
# ---------------------------------------------------------------------------

class TestGetCounterPackage:
    def test_returns_counter_for_known_archetype(self):
        arch = Archetype(label=ArchetypeLabel.AGGRESSOR, confidence=0.8)
        pkg = get_counter_package(arch)

        assert isinstance(pkg, CounterPackage)
        assert pkg.target_archetype == ArchetypeLabel.AGGRESSOR
        assert len(pkg.strategies) > 0
        assert len(pkg.plays_to_exploit) > 0

    def test_returns_fallback_for_unknown(self):
        arch = Archetype(label=ArchetypeLabel.UNKNOWN, confidence=0.0)
        pkg = get_counter_package(arch)

        assert pkg.target_archetype == ArchetypeLabel.UNKNOWN
        assert pkg.confidence == 0.0

    @pytest.mark.parametrize(
        "label",
        [
            ArchetypeLabel.TURTLE,
            ArchetypeLabel.COUNTER_PUNCHER,
            ArchetypeLabel.CHAOS_AGENT,
            ArchetypeLabel.META_SLAVE,
            ArchetypeLabel.ADAPTIVE,
            ArchetypeLabel.ONE_TRICK,
        ],
    )
    def test_counter_package_exists_for_all_archetypes(self, label):
        arch = Archetype(label=label, confidence=0.9)
        pkg = get_counter_package(arch)

        assert pkg.target_archetype == label
        assert len(pkg.strategies) > 0


# ---------------------------------------------------------------------------
# update_mid_game
# ---------------------------------------------------------------------------

class TestUpdateMidGame:
    def test_refines_with_new_signals(self):
        initial = classify_opponent({"signals": ["high tempo"], "title": "madden26"})
        updated = update_mid_game(initial, ["risk-taking", "blitz-heavy", "deep shots"])

        assert isinstance(updated, Archetype)
        assert updated.label == ArchetypeLabel.AGGRESSOR
        assert updated.confidence >= initial.confidence

    def test_can_change_archetype(self):
        initial = Archetype(
            label=ArchetypeLabel.UNKNOWN,
            confidence=0.0,
            traits=[],
            title="madden26",
        )
        updated = update_mid_game(initial, ["conservative", "clock-management", "run-heavy"])

        assert updated.label == ArchetypeLabel.TURTLE


# ---------------------------------------------------------------------------
# get_archetype_library
# ---------------------------------------------------------------------------

class TestGetArchetypeLibrary:
    def test_returns_all_archetypes(self):
        library = get_archetype_library("madden26")

        assert isinstance(library, list)
        assert len(library) == 7  # all non-UNKNOWN archetypes
        labels = {a.label for a in library}
        assert ArchetypeLabel.AGGRESSOR in labels
        assert ArchetypeLabel.TURTLE in labels
        assert ArchetypeLabel.UNKNOWN not in labels

    def test_all_have_title(self):
        library = get_archetype_library("cfb26")

        for arch in library:
            assert arch.title == "cfb26"

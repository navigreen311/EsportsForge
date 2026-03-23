"""Tests for Ratings Update Impact Alerts service."""

from __future__ import annotations

import pytest

from app.services.agents.madden26 import ratings_alerts


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_stores():
    """Reset in-memory stores before each test."""
    ratings_alerts.reset_store()
    yield
    ratings_alerts.reset_store()


def _sample_patch_notes(num_changes: int = 3) -> dict:
    """Build sample patch notes with the given number of changes."""
    changes = []
    for i in range(num_changes):
        changes.append({
            "player_name": f"Player_{i}",
            "attribute": "speed" if i % 2 == 0 else "awareness",
            "old_value": 85,
            "new_value": 85 + (i * 2 - 1),  # alternating buff/nerf pattern
        })
    return {"patch_version": "1.05", "changes": changes}


def _big_delta_changes() -> list[dict]:
    """Changes with large deltas for testing significance thresholds."""
    return [
        {"player_name": "Star_QB", "attribute": "throw_power", "old_value": 90, "new_value": 96, "delta": 6},
        {"player_name": "Backup_WR", "attribute": "speed", "old_value": 82, "new_value": 80, "delta": -2},
        {"player_name": "Star_RB", "attribute": "agility", "old_value": 88, "new_value": 82, "delta": -6},
    ]


# ---------------------------------------------------------------------------
# check_patch_impact
# ---------------------------------------------------------------------------

def test_check_patch_impact_returns_correct_structure():
    """check_patch_impact returns all expected keys."""
    patch = _sample_patch_notes(2)
    result = ratings_alerts.check_patch_impact(patch)

    assert result["patch_version"] == "1.05"
    assert result["total_changes"] == 2
    assert "significant_changes" in result
    assert "rating_changes" in result
    assert "analyzed_at" in result


def test_check_patch_impact_identifies_significant_changes():
    """Changes with abs(delta) >= 3 are flagged as significant."""
    patch = {
        "patch_version": "2.00",
        "changes": [
            {"player_name": "A", "attribute": "speed", "old_value": 80, "new_value": 84},  # +4 sig
            {"player_name": "B", "attribute": "speed", "old_value": 80, "new_value": 81},  # +1 not sig
            {"player_name": "C", "attribute": "speed", "old_value": 80, "new_value": 75},  # -5 sig
        ],
    }
    result = ratings_alerts.check_patch_impact(patch)

    assert result["total_changes"] == 3
    assert len(result["significant_changes"]) == 2
    sig_names = {c["player_name"] for c in result["significant_changes"]}
    assert sig_names == {"A", "C"}


def test_check_patch_impact_classifies_direction():
    """Each change should be classified as buff, nerf, or unchanged."""
    patch = {
        "patch_version": "1.01",
        "changes": [
            {"player_name": "Up", "attribute": "ovr", "old_value": 80, "new_value": 85},
            {"player_name": "Down", "attribute": "ovr", "old_value": 80, "new_value": 75},
            {"player_name": "Same", "attribute": "ovr", "old_value": 80, "new_value": 80},
        ],
    }
    result = ratings_alerts.check_patch_impact(patch)
    directions = {c["player_name"]: c["direction"] for c in result["rating_changes"]}

    assert directions["Up"] == "buff"
    assert directions["Down"] == "nerf"
    assert directions["Same"] == "unchanged"


def test_check_patch_impact_empty_changes():
    """Empty changes list should return zero counts."""
    result = ratings_alerts.check_patch_impact({"patch_version": "0.01", "changes": []})
    assert result["total_changes"] == 0
    assert result["significant_changes"] == []


# ---------------------------------------------------------------------------
# get_affected_gameplans
# ---------------------------------------------------------------------------

def test_get_affected_gameplans_returns_affected():
    """get_affected_gameplans returns affected gameplan stubs."""
    changes = _big_delta_changes()
    result = ratings_alerts.get_affected_gameplans("user-42", changes)

    assert result["user_id"] == "user-42"
    assert result["total_affected"] > 0
    assert len(result["affected_gameplans"]) == result["total_affected"]

    # Each affected gameplan should reference a player
    for gp in result["affected_gameplans"]:
        assert "gameplan_id" in gp
        assert "affected_player" in gp
        assert "impact_level" in gp


def test_get_affected_gameplans_empty_changes():
    """No changes means no affected gameplans."""
    result = ratings_alerts.get_affected_gameplans("user-99", [])
    assert result["total_affected"] == 0
    assert result["affected_gameplans"] == []


# ---------------------------------------------------------------------------
# generate_impact_report
# ---------------------------------------------------------------------------

def test_generate_impact_report_structure():
    """generate_impact_report returns a well-structured report."""
    changes = _big_delta_changes()
    report = ratings_alerts.generate_impact_report(changes)

    assert "report_id" in report
    assert len(report["report_id"]) == 12
    assert report["total_changes"] == 3
    assert len(report["buffs"]) == 1  # Star_QB +6
    assert len(report["nerfs"]) == 2  # Backup_WR -2, Star_RB -6
    assert "meta_implications" in report
    assert "generated_at" in report


def test_generate_impact_report_detects_major_swing():
    """Major rating swings (abs >= 5) trigger meta shift implication."""
    changes = [
        {"player_name": "X", "attribute": "speed", "delta": 7},
    ]
    report = ratings_alerts.generate_impact_report(changes)

    implications = report["meta_implications"]
    assert any("Major rating swings" in imp for imp in implications)


# ---------------------------------------------------------------------------
# auto_adjust_recommendations
# ---------------------------------------------------------------------------

def test_auto_adjust_skips_minor_changes():
    """Changes with abs(delta) < 2 are skipped."""
    changes = [
        {"player_name": "Minor", "attribute": "speed", "delta": 1},
        {"player_name": "Major", "attribute": "speed", "delta": 5},
    ]
    result = ratings_alerts.auto_adjust_recommendations("user-1", changes)

    assert result["total_adjustments"] == 1
    assert result["adjustments"][0]["player_name"] == "Major"


def test_auto_adjust_buff_vs_nerf_recommendations():
    """Buffs and nerfs produce different recommendation text."""
    changes = [
        {"player_name": "Buffed", "attribute": "speed", "delta": 4},
        {"player_name": "Nerfed", "attribute": "speed", "delta": -4},
    ]
    result = ratings_alerts.auto_adjust_recommendations("user-2", changes)

    recs = {a["player_name"]: a["recommendation"] for a in result["adjustments"]}
    assert "featuring" in recs["Buffed"].lower() or "boosted" in recs["Buffed"].lower()
    assert "reduce" in recs["Nerfed"].lower() or "dropped" in recs["Nerfed"].lower()


def test_auto_adjust_priority_levels():
    """High priority for abs(delta) >= 5, medium otherwise."""
    changes = [
        {"player_name": "Big", "attribute": "ovr", "delta": 6},
        {"player_name": "Small", "attribute": "ovr", "delta": 3},
    ]
    result = ratings_alerts.auto_adjust_recommendations("user-3", changes)

    priorities = {a["player_name"]: a["priority"] for a in result["adjustments"]}
    assert priorities["Big"] == "high"
    assert priorities["Small"] == "medium"

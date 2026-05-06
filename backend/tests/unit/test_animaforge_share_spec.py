"""Unit tests for AnimaForge share-win spec builder (Agent #9)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.animaforge.share_spec import (
    BRAND_ACCENT,
    BRAND_BACKGROUND,
    FPS,
    RESOLUTION,
    build_share_card_spec,
)


@pytest.fixture
def user():
    return SimpleNamespace(
        id="user-1",
        email="ivan@example.com",
        username="ivann",
        display_name="Ivan",
    )


def _assert_brand(spec: dict) -> None:
    assert spec["resolution"] == RESOLUTION
    assert spec["fps"] == FPS
    assert spec["background"] == BRAND_BACKGROUND
    assert spec["accent_color"] == BRAND_ACCENT
    assert spec["logo"] == "esportsforge-white"
    assert spec["watermark"] == "esportsforge.gg"
    assert "gamertag" in spec
    assert isinstance(spec["sequence"], list) and spec["sequence"]
    assert isinstance(spec["share_text"], str) and spec["share_text"]
    assert isinstance(spec["hashtags"], list) and "#EsportsForge" in spec["hashtags"]


def test_tournament_win(user):
    spec = build_share_card_spec(
        "tournament-win",
        {"tournament_name": "Spring Madness", "record": "5-0", "title_id": "madden-26"},
        user,
    )
    assert spec["template"] == "tournament-win-card"
    assert spec["duration"] == 20
    _assert_brand(spec)
    assert "Spring Madness" in spec["share_text"]
    # Sequence covers the trophy + reveals.
    actions = [step["action"] for step in spec["sequence"]]
    assert "trophy-animation" in actions
    assert "gamertag-reveal" in actions
    assert "cta" in actions


def test_benchmark_milestone(user):
    spec = build_share_card_spec(
        "benchmark-milestone",
        {"skill": "Pre-Snap Read", "percentile": 8, "title_id": "madden-26"},
        user,
    )
    assert spec["template"] == "percentile-milestone-card"
    assert spec["duration"] == 15
    _assert_brand(spec)
    assert "Top 8%" in spec["share_text"]
    assert "Pre-Snap Read" in spec["share_text"]
    actions = [step["action"] for step in spec["sequence"]]
    assert "meter-fill" in actions
    assert "skill-reveal" in actions


def test_win_streak(user):
    spec = build_share_card_spec(
        "win-streak",
        {"streak": 10, "title_id": "nba-2k26"},
        user,
    )
    assert spec["template"] == "win-streak-card"
    assert spec["duration"] == 15
    _assert_brand(spec)
    assert "10-game win streak" in spec["share_text"]
    assert "#WinStreak" in spec["hashtags"]
    actions = [step["action"] for step in spec["sequence"]]
    assert "counter-animate" in actions


def test_impactrank_fix(user):
    spec = build_share_card_spec(
        "impactrank-fix",
        {"fix_name": "Red Zone", "improvement": 4.5, "title_id": "madden-26"},
        user,
    )
    assert spec["template"] == "improvement-card"
    assert spec["duration"] == 20
    _assert_brand(spec)
    assert "4.5%" in spec["share_text"]
    assert "#ImpactRank" in spec["hashtags"]
    actions = [step["action"] for step in spec["sequence"]]
    assert "before-bar" in actions
    assert "after-bar" in actions
    assert "fix-name-reveal" in actions


def test_playertwin_milestone(user):
    spec = build_share_card_spec(
        "playertwin-milestone",
        {"accuracy": 0.78, "games_played": 30, "title_id": "madden-26"},
        user,
    )
    assert spec["template"] == "playertwin-milestone-card"
    assert spec["duration"] == 15
    _assert_brand(spec)
    assert "78% accuracy" in spec["share_text"]
    assert "#PlayerTwin" in spec["hashtags"]
    actions = [step["action"] for step in spec["sequence"]]
    assert "twin-gauge-fill" in actions


def test_unknown_trigger_returns_fallback(user):
    spec = build_share_card_spec("brand-new-trigger", {"title_id": "madden-26"}, user)
    assert spec["template"] == "milestone-card"
    _assert_brand(spec)


def test_handles_user_as_dict():
    spec = build_share_card_spec(
        "win-streak",
        {"streak": 5, "title_id": "madden-26"},
        {"display_name": "Phantom", "email": "phantom@example.com"},
    )
    assert spec["gamertag"] == "Phantom"


def test_handles_missing_user():
    spec = build_share_card_spec("win-streak", {"streak": 5, "title_id": "madden-26"}, None)
    assert spec["gamertag"] == "Player"

"""Unit tests for the AnimaForge weapon animation spec builder.

Agent #4 — covers all 11 titles from `backend/app/models/secret_weapon.py`
TITLE_IDS plus the cfb-26 → madden reuse and the unknown-title fallback.

The builder is a pure function so these tests don't require Agent #1's
service / model modules to be merged.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.animaforge.weapon_spec import build_weapon_animation_spec


def _make_weapon(title_id: str) -> SimpleNamespace:
    """Build a weapon-like duck-typed object covering every field the
    spec builder reads off `SecretWeapon`."""
    return SimpleNamespace(
        id="wpn-test-123",
        title_id=title_id,
        play_name="Test Play",
        formation="Singleback Ace",
        instructions=["Step 1", "Step 2"],
        setup_steps=["Motion Z left", "Audible to slant"],
        description="Voiceover description",
    )


# ---------------------------------------------------------------------------
# Per-title coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "title_id, expected_template, expected_duration, expected_style_key",
    [
        ("madden-26",   "football-play-diagram",   12, "gapHighlight"),
        ("cfb-26",      "football-play-diagram",   12, "gapHighlight"),  # reuses madden
        ("nba-2k26",    "basketball-play-diagram", 10, "screenPath"),
        ("eafc-26",     "soccer-play-diagram",     12, "ballPath"),
        ("mlb-26",      "baseball-play-diagram",    9, "ballTrajectory"),
        ("warzone",     "fps-tactical-diagram",    14, "squadMarkers"),
        ("fortnite",    "fortnite-build-diagram",  11, "buildSequence"),
        ("ufc-5",       "fighting-combo-diagram",   9, "strikePaths"),
        ("pga-2k25",    "golf-shot-diagram",       10, "ballFlight"),
        ("undisputed",  "boxing-combo-diagram",     9, "punchPaths"),
        ("video-poker", "card-hold-diagram",        7, "cardHighlight"),
    ],
)
def test_spec_per_title(
    title_id: str,
    expected_template: str,
    expected_duration: int,
    expected_style_key: str,
) -> None:
    """Each of the 11 titles produces the contracted template, duration, and
    at least one title-specific style key."""
    weapon = _make_weapon(title_id)
    spec = build_weapon_animation_spec(weapon)

    assert spec["template"] == expected_template, (
        f"{title_id}: expected template {expected_template!r}, got {spec['template']!r}"
    )
    assert spec["duration"] == expected_duration, (
        f"{title_id}: expected duration {expected_duration}, got {spec['duration']}"
    )
    assert "style" in spec, f"{title_id}: spec missing 'style' block"
    assert expected_style_key in spec["style"], (
        f"{title_id}: style missing key {expected_style_key!r}; "
        f"got keys {sorted(spec['style'])}"
    )


# ---------------------------------------------------------------------------
# Common-field plumbing — ensures weapon data flows into the spec
# ---------------------------------------------------------------------------


def test_common_fields_are_populated() -> None:
    """The common block (playName/formation/voiceover/branding) is filled
    from the weapon for every title."""
    weapon = _make_weapon("madden-26")
    spec = build_weapon_animation_spec(weapon)

    assert spec["playName"] == "Test Play"
    assert spec["formation"] == "Singleback Ace"
    assert spec["executionPath"] == ["Step 1", "Step 2"]
    assert spec["setupMotions"] == ["Motion Z left", "Audible to slant"]
    assert spec["voiceoverText"] == "Voiceover description"
    assert spec["highlightColor"] == "#4ADE80"
    assert spec["brandColor"] == "#0A0C10"
    assert spec["logo"] == "esportsforge"


# ---------------------------------------------------------------------------
# Fallback — unknown title uses the madden template (per contract §9)
# ---------------------------------------------------------------------------


def test_unknown_title_falls_back_to_madden() -> None:
    weapon = _make_weapon("not-a-real-title")
    spec = build_weapon_animation_spec(weapon)
    assert spec["template"] == "football-play-diagram"
    assert spec["duration"] == 12


def test_missing_title_id_falls_back_to_madden() -> None:
    """A weapon without a title_id (defensive fallback) still builds a
    valid madden-style spec."""
    weapon = SimpleNamespace(
        id="wpn-x",
        title_id=None,
        play_name=None,
        formation=None,
        instructions=None,
        setup_steps=None,
        description=None,
    )
    spec = build_weapon_animation_spec(weapon)
    assert spec["template"] == "football-play-diagram"
    # Empty list / None handling
    assert spec["executionPath"] == []
    assert spec["setupMotions"] == []

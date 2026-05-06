"""Unit tests for the AnimaForge drill animation spec builder.

Covers:
- At least one combo per title with any spec entry (12 titles incl. cfb-26).
- Returns ``None`` for unknown titles, unknown drill types, and bad input.
- Returned dicts are deep copies (mutating one does not pollute the table).
- Every entry has the required structural fields (template, sequence,
  voiceover, duration).
- The 11 canonical title IDs from secret_weapon all surface drill specs
  (every title in :data:`TITLE_IDS` appears in DRILL_ANIMATION_SPECS).
"""

from __future__ import annotations

import pytest

from app.models.secret_weapon import TITLE_IDS
from app.services.animaforge.drill_spec import (
    DRILL_ANIMATION_SPECS,
    build_drill_animation_spec,
)


# ---------------------------------------------------------------------------
# Per-title coverage — one combo per title
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "title_id,drill_type",
    [
        ("madden-26", "pre-snap-reads"),
        ("madden-26", "blitz-timing"),
        ("madden-26", "red-zone-execution"),
        ("cfb-26", "pre-snap-reads"),
        ("cfb-26", "blitz-timing"),
        ("cfb-26", "red-zone-execution"),
        ("nba-2k26", "on-ball-defense"),
        ("nba-2k26", "pnr-coverage"),
        ("nba-2k26", "shot-timing"),
        ("eafc-26", "jockey-timing"),
        ("eafc-26", "skill-move"),
        ("mlb-26", "pitch-sequence"),
        ("warzone", "movement-tech"),
        ("fortnite", "edit-speed"),
        ("ufc-5", "takedown-defense"),
        ("pga-2k25", "shot-shape"),
        ("undisputed", "parry-timing"),
        ("video-poker", "optimal-hold"),
    ],
)
def test_build_spec_returns_dict_for_known_combos(
    title_id: str, drill_type: str
) -> None:
    spec = build_drill_animation_spec(title_id, drill_type)
    assert spec is not None, f"missing spec for ({title_id}, {drill_type})"
    assert isinstance(spec, dict)


# ---------------------------------------------------------------------------
# Required fields on every spec
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = ("template", "sequence", "voiceover", "duration")


@pytest.mark.parametrize(
    "title_id,by_drill",
    list(DRILL_ANIMATION_SPECS.items()),
)
def test_every_spec_has_required_fields(
    title_id: str, by_drill: dict[str, dict]
) -> None:
    for drill_type, spec in by_drill.items():
        for field in REQUIRED_FIELDS:
            assert field in spec, (
                f"{title_id}:{drill_type} missing {field!r}"
            )
        assert isinstance(spec["sequence"], list)
        assert len(spec["sequence"]) >= 1
        assert isinstance(spec["duration"], int) and spec["duration"] > 0


# ---------------------------------------------------------------------------
# Unknown / invalid combos return None (graceful degradation)
# ---------------------------------------------------------------------------

def test_unknown_title_returns_none() -> None:
    assert build_drill_animation_spec("not-a-title", "pre-snap-reads") is None


def test_unknown_drill_for_known_title_returns_none() -> None:
    assert build_drill_animation_spec("madden-26", "no-such-drill") is None


def test_known_drill_for_wrong_title_returns_none() -> None:
    # "shot-timing" exists for nba-2k26, not for madden-26.
    assert build_drill_animation_spec("madden-26", "shot-timing") is None


def test_empty_strings_return_none() -> None:
    assert build_drill_animation_spec("", "") is None
    assert build_drill_animation_spec("madden-26", "") is None
    assert build_drill_animation_spec("", "pre-snap-reads") is None


# ---------------------------------------------------------------------------
# Deep-copy guarantee — caller mutations don't pollute the table
# ---------------------------------------------------------------------------

def test_returned_spec_is_deep_copy() -> None:
    spec_a = build_drill_animation_spec("madden-26", "pre-snap-reads")
    assert spec_a is not None
    original_voiceover = spec_a["voiceover"]
    original_first_step_action = spec_a["sequence"][0]["action"]

    # Mutate the returned dict aggressively.
    spec_a["voiceover"] = "MUTATED"
    spec_a["sequence"][0]["action"] = "MUTATED"
    spec_a["sequence"].append({"step": 999, "action": "INJECTED"})

    # Fetch a fresh copy — table must be untouched.
    spec_b = build_drill_animation_spec("madden-26", "pre-snap-reads")
    assert spec_b is not None
    assert spec_b["voiceover"] == original_voiceover
    assert spec_b["sequence"][0]["action"] == original_first_step_action
    assert all(step.get("action") != "INJECTED" for step in spec_b["sequence"])


# ---------------------------------------------------------------------------
# CFB 26 reuses Madden 26's specs (per blueprint Section 9 reuse rule)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "drill_type",
    ["pre-snap-reads", "blitz-timing", "red-zone-execution"],
)
def test_cfb_26_reuses_madden_26_specs(drill_type: str) -> None:
    madden = build_drill_animation_spec("madden-26", drill_type)
    cfb = build_drill_animation_spec("cfb-26", drill_type)
    assert madden == cfb


def test_cfb_26_and_madden_26_are_independent_objects() -> None:
    """Reuse must be a deep copy — mutating CFB shouldn't touch Madden."""
    cfb = build_drill_animation_spec("cfb-26", "pre-snap-reads")
    assert cfb is not None
    cfb["voiceover"] = "CFB ONLY"
    madden = build_drill_animation_spec("madden-26", "pre-snap-reads")
    assert madden is not None
    assert madden["voiceover"] != "CFB ONLY"


# ---------------------------------------------------------------------------
# Title coverage — every canonical title has at least one drill spec
# ---------------------------------------------------------------------------

def test_all_canonical_titles_have_at_least_one_drill_spec() -> None:
    missing = [t for t in TITLE_IDS if t not in DRILL_ANIMATION_SPECS]
    assert not missing, f"titles missing from DRILL_ANIMATION_SPECS: {missing}"

    for title_id in TITLE_IDS:
        assert len(DRILL_ANIMATION_SPECS[title_id]) >= 1, (
            f"{title_id} has no drill specs"
        )

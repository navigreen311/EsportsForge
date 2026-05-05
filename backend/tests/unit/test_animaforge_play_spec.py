"""Unit tests for the AnimaForge play-diagram spec builder (Agent #8)."""

from __future__ import annotations

import pytest

from app.services.animaforge.play_spec import (
    build_play_diagram_spec,
    extract_player_paths,
    extract_player_runs,
    extract_routes_from_tags,
    get_void_for_coverage,
)


# ---------------------------------------------------------------------------
# Coverage helpers
# ---------------------------------------------------------------------------


class TestGetVoidForCoverage:
    def test_cover_3(self) -> None:
        assert (
            get_void_for_coverage("cover-3")
            == "middle-of-field-under-safeties"
        )

    def test_cover_2(self) -> None:
        assert (
            get_void_for_coverage("cover-2") == "deep-halves-above-corners"
        )

    def test_man(self) -> None:
        assert get_void_for_coverage("man") == "pick-route-separation"

    def test_unknown_coverage_falls_back(self) -> None:
        assert get_void_for_coverage("alien-defense") == "standard-reads"

    def test_none_coverage_falls_back(self) -> None:
        assert get_void_for_coverage(None) == "standard-reads"

    def test_case_insensitive(self) -> None:
        assert (
            get_void_for_coverage("Cover-3")
            == "middle-of-field-under-safeties"
        )


# ---------------------------------------------------------------------------
# Tag extractors
# ---------------------------------------------------------------------------


def test_extract_routes_from_tags_maps_known_tags() -> None:
    routes = extract_routes_from_tags(["deep-shot", "play-action"])
    assert routes == [
        {"receiver": "X", "route": "go"},
        {"receiver": "Z", "route": "post"},
    ]


def test_extract_routes_from_tags_empty_returns_default() -> None:
    routes = extract_routes_from_tags([])
    assert len(routes) == 1
    assert routes[0]["route"] == "curl"


def test_extract_player_paths_default() -> None:
    paths = extract_player_paths(None)
    assert paths == [{"player": "PG", "path": "iso-drive"}]


def test_extract_player_runs_default() -> None:
    runs = extract_player_runs(None)
    assert runs == [{"player": "ST", "run": "through-ball"}]


# ---------------------------------------------------------------------------
# Per-title template branches
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("title_id", ["madden-26", "cfb-26"])
def test_football_titles_use_route_diagram_template(title_id: str) -> None:
    spec = build_play_diagram_spec(
        {
            "play_name": "PA Crossers",
            "formation": "Gun Trips TE",
            "tags": ["play-action", "zone-beater"],
            "call_structure": {"layer1": "Read MOFO/MOFC", "layer2": []},
            "title_id": title_id,
            "opponent_coverage": "cover-3",
        }
    )
    assert spec["template"] == "football-route-diagram"
    assert spec["formation"] == "Gun Trips TE"
    assert spec["playName"] == "PA Crossers"
    # Coverage overlay actually wires through the void helper.
    assert spec["voidHighlight"] == "middle-of-field-under-safeties"
    assert spec["readProgression"] == "Read MOFO/MOFC"
    # Style block carries the canonical color palette.
    assert spec["style"]["voidColor"] == "#F59E0B"


def test_basketball_template() -> None:
    spec = build_play_diagram_spec(
        {
            "play_name": "Horns Flare",
            "formation": "Horns",
            "tags": ["screen", "cut"],
            "title_id": "nba-2k26",
        }
    )
    assert spec["template"] == "basketball-set-diagram"
    assert spec["setName"] == "Horns Flare"
    assert isinstance(spec["playerPaths"], list)
    assert spec["playerPaths"][0]["player"] == "PG"


def test_soccer_template() -> None:
    spec = build_play_diagram_spec(
        {
            "play_name": "Wing Overload",
            "formation": "4-3-3",
            "tags": ["through-ball", "overlap"],
            "title_id": "eafc-26",
        }
    )
    assert spec["template"] == "soccer-play-diagram"
    assert spec["formationShape"] == "4-3-3"
    assert spec["passLine"] == "animated-dotted"


@pytest.mark.parametrize(
    "title_id",
    [
        "mlb-26",
        "warzone",
        "fortnite",
        "ufc-5",
        "pga-2k25",
        "undisputed",
        "video-poker",
        "completely-unknown-title",
    ],
)
def test_universal_fallback_for_remaining_titles(title_id: str) -> None:
    spec = build_play_diagram_spec(
        {
            "play_name": "Generic Tactic",
            "title_id": title_id,
            "call_structure": {"layer1": "Step 1", "layer2": "Step 2"},
        }
    )
    assert spec["template"] == "universal-tactic-diagram"
    assert spec["playName"] == "Generic Tactic"
    assert spec["duration"] == 10


# ---------------------------------------------------------------------------
# Coverage-variance assertion (the whole point of per-coverage caching)
# ---------------------------------------------------------------------------


def test_same_play_different_coverage_produces_different_void() -> None:
    base = {
        "play_name": "PA Crossers",
        "formation": "Gun Trips TE",
        "tags": ["play-action"],
        "title_id": "madden-26",
    }
    spec_c3 = build_play_diagram_spec({**base, "opponent_coverage": "cover-3"})
    spec_man = build_play_diagram_spec({**base, "opponent_coverage": "man"})

    assert spec_c3["voidHighlight"] != spec_man["voidHighlight"]


def test_missing_call_structure_does_not_raise() -> None:
    spec = build_play_diagram_spec(
        {
            "play_name": "X",
            "title_id": "madden-26",
        }
    )
    assert spec["readProgression"] is None
    assert spec["audibles"] is None


def test_title_id_case_normalised() -> None:
    spec = build_play_diagram_spec(
        {"play_name": "X", "title_id": "MADDEN-26"}
    )
    assert spec["template"] == "football-route-diagram"

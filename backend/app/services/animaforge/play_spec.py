"""AnimaForge play-diagram spec builder.

Per blueprint Section 4. Translates a Gameplan Play (name, formation, tags,
call structure, opponent coverage, title) into the animation spec the
AnimaForge `/api/v1/render` endpoint expects.

Branches by title:
  - madden-26 / cfb-26 -> football-route-diagram (with coverage overlay)
  - nba-2k26           -> basketball-set-diagram
  - eafc-26            -> soccer-play-diagram
  - * (everything else) -> universal-tactic-diagram
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------

OFFENSE_COLOR = "#4ADE80"
DEFENSE_COLOR = "#EF4444"
VOID_COLOR = "#F59E0B"
PASS_COLOR = "#22D3EE"

FOOTBALL_TITLES = ("madden-26", "cfb-26")


# ---------------------------------------------------------------------------
# Coverage helpers (verbatim from blueprint Section 4 helpers)
# ---------------------------------------------------------------------------


COVERAGE_VOIDS: dict[str, str] = {
    "cover-3": "middle-of-field-under-safeties",
    "cover-2": "deep-halves-above-corners",
    "cover-1": "natural-rub-underneath",
    "man": "pick-route-separation",
    "cover-4": "crossers-underneath",
}


def get_void_for_coverage(coverage: str | None) -> str:
    """Return the canonical void-zone label for a coverage shell.

    Falls back to "standard-reads" when the coverage is unknown or `None`.
    """
    if not coverage:
        return "standard-reads"
    return COVERAGE_VOIDS.get(coverage.lower(), "standard-reads")


# ---------------------------------------------------------------------------
# Tag extraction helpers
# ---------------------------------------------------------------------------


# Concept tags that imply specific football route shapes. The animator turns
# each into a route line — order is preserved so the receiver mapping is
# deterministic across renders.
_ROUTE_TAG_MAP: dict[str, str] = {
    "deep-shot": "go",
    "play-action": "post",
    "man-beater": "slant",
    "zone-beater": "curl",
    "quick-pass": "slant",
    "screen": "screen",
    "rpo": "bubble",
    "draw": "delay",
    "run": "dive",
    "misdirection": "drag",
}


def extract_routes_from_tags(tags: list[str] | None) -> list[dict[str, str]]:
    """Convert concept tags to a list of `{receiver, route}` dicts.

    Receivers are positional (X, Z, slot1, slot2, TE) so the AnimaForge
    template can map each to a player icon. We always emit at least one
    route so the renderer never gets an empty diagram.
    """
    if not tags:
        return [{"receiver": "X", "route": "curl"}]

    receivers = ["X", "Z", "slot1", "slot2", "TE"]
    routes: list[dict[str, str]] = []
    for tag in tags:
        route = _ROUTE_TAG_MAP.get(tag)
        if route is None:
            continue
        receiver = receivers[len(routes) % len(receivers)]
        routes.append({"receiver": receiver, "route": route})

    if not routes:
        routes.append({"receiver": "X", "route": "curl"})
    return routes


def extract_player_paths(tags: list[str] | None) -> list[dict[str, str]]:
    """Basketball: convert tags to cut/screen path descriptors."""
    if not tags:
        return [{"player": "PG", "path": "iso-drive"}]
    out: list[dict[str, str]] = []
    positions = ["PG", "SG", "SF", "PF", "C"]
    for i, tag in enumerate(tags):
        out.append({"player": positions[i % len(positions)], "path": tag})
    return out or [{"player": "PG", "path": "iso-drive"}]


def extract_player_runs(tags: list[str] | None) -> list[dict[str, str]]:
    """Soccer: convert tags to runner path descriptors."""
    if not tags:
        return [{"player": "ST", "run": "through-ball"}]
    out: list[dict[str, str]] = []
    roles = ["ST", "LW", "RW", "CAM", "CM"]
    for i, tag in enumerate(tags):
        out.append({"player": roles[i % len(roles)], "run": tag})
    return out or [{"player": "ST", "run": "through-ball"}]


# ---------------------------------------------------------------------------
# Call structure extraction
# ---------------------------------------------------------------------------


def _layer(call_structure: Any, key: str) -> Any:
    """Best-effort fetch of `call_structure.layerN` from dict-or-attr objects.

    `call_structure` may be a dict pulled from JSON or a Pydantic-style
    object. Return `None` if absent rather than raising — the spec builder
    tolerates missing layers.
    """
    if call_structure is None:
        return None
    if isinstance(call_structure, dict):
        return call_structure.get(key)
    return getattr(call_structure, key, None)


# ---------------------------------------------------------------------------
# Per-title spec builders
# ---------------------------------------------------------------------------


def _football_spec(
    *,
    play_name: str,
    formation: str | None,
    tags: list[str] | None,
    call_structure: Any,
    opponent_coverage: str | None,
) -> dict[str, Any]:
    """Madden / CFB football route diagram with coverage overlay."""
    return {
        "template": "football-route-diagram",
        "formation": formation or "Gun Spread",
        "playName": play_name,
        "routes": extract_routes_from_tags(tags),
        "defense": opponent_coverage or "unknown",
        "voidHighlight": get_void_for_coverage(opponent_coverage),
        "readProgression": _layer(call_structure, "layer1"),
        "audibles": _layer(call_structure, "layer2"),
        "duration": 12,
        "style": {
            "offenseColor": OFFENSE_COLOR,
            "defenseColor": DEFENSE_COLOR,
            "voidColor": VOID_COLOR,
            "background": "field-top-down",
            "routeAnimation": "smooth-path",
            "defenseAnimation": "coverage-zones",
        },
    }


def _basketball_spec(
    *,
    play_name: str,
    formation: str | None,
    tags: list[str] | None,
) -> dict[str, Any]:
    """NBA 2K basketball set diagram."""
    return {
        "template": "basketball-set-diagram",
        "setName": play_name,
        "formation": formation or "Horns",
        "playerPaths": extract_player_paths(tags),
        "duration": 10,
        "style": {
            "background": "court-top-down",
            "cutColor": OFFENSE_COLOR,
            "screenColor": VOID_COLOR,
        },
    }


def _soccer_spec(
    *,
    play_name: str,
    formation: str | None,
    tags: list[str] | None,
) -> dict[str, Any]:
    """EA FC soccer play diagram."""
    return {
        "template": "soccer-play-diagram",
        "playName": play_name,
        "formationShape": formation or "4-3-3",
        "playerRuns": extract_player_runs(tags),
        "passLine": "animated-dotted",
        "duration": 12,
        "style": {
            "background": "pitch-top-down",
            "runColor": OFFENSE_COLOR,
            "passColor": PASS_COLOR,
        },
    }


def _universal_spec(
    *,
    play_name: str,
    call_structure: Any,
) -> dict[str, Any]:
    """Catch-all for titles without a dedicated template."""
    return {
        "template": "universal-tactic-diagram",
        "playName": play_name,
        "steps": call_structure or {},
        "duration": 10,
        "style": {
            "background": "neutral-grid",
            "accentColor": OFFENSE_COLOR,
        },
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def build_play_diagram_spec(params: dict[str, Any]) -> dict[str, Any]:
    """Build the AnimaForge animation spec for a single play.

    Expected `params` keys (any may be missing — defaults applied):
      - play_name (str)        — required
      - formation (str)        — optional
      - tags (list[str])       — optional, used to derive routes/paths
      - call_structure (dict)  — optional, layer1 = read progression
      - title_id (str)         — required, picks the template branch
      - opponent_coverage (str) — optional, defaults to "standard-reads" void

    Returns a JSON-serialisable dict ready to send as
    `AnimaForgeService.request_render(spec=...)`.
    """
    play_name: str = params.get("play_name") or "Untitled Play"
    formation: str | None = params.get("formation")
    tags: list[str] | None = params.get("tags")
    call_structure: Any = params.get("call_structure")
    title_id: str = (params.get("title_id") or "").lower()
    opponent_coverage: str | None = params.get("opponent_coverage")

    if title_id in FOOTBALL_TITLES:
        return _football_spec(
            play_name=play_name,
            formation=formation,
            tags=tags,
            call_structure=call_structure,
            opponent_coverage=opponent_coverage,
        )

    if title_id == "nba-2k26":
        return _basketball_spec(
            play_name=play_name,
            formation=formation,
            tags=tags,
        )

    if title_id == "eafc-26":
        return _soccer_spec(
            play_name=play_name,
            formation=formation,
            tags=tags,
        )

    # All other titles fall through to the universal diagram. This includes
    # mlb-26, warzone, fortnite, ufc-5, pga-2k25, undisputed, video-poker.
    # If/when those titles get bespoke per-play templates, add a branch above.
    return _universal_spec(play_name=play_name, call_structure=call_structure)

"""
template_routes — hand-authored route geometry for the built-in template plays.

The AI path emits routes per play (validated via `route_validator`). The
template fallback has no LLM, so these curated routes let a generated gameplan
still carry real geometry end-to-end (backend → frontend animated diagram) even
with no ANTHROPIC_API_KEY. Keyed by play name.

Coordinate space: 0–100 × 0–100, LOS at y=60, offense below, routes run up
(decreasing y). Same contract as `RouteSpec` / the frontend `DiagramRoute`.
"""

from __future__ import annotations

from typing import Optional

from app.schemas.madden26.gameplan import RouteSpec

# raw {receiver: points} per play, converted to RouteSpec at import.
_RAW: dict[str, dict[str, list[list[float]]]] = {
    "Mesh Cross": {
        "X": [[12, 60], [12, 56], [64, 53]],
        "Z": [[88, 60], [88, 56], [34, 53]],
        "SL": [[30, 59], [30, 45], [18, 38]],
        "TE": [[62, 60], [62, 49], [62, 52]],
        "HB": [[46, 72], [46, 68], [66, 66]],
    },
    "Four Verticals": {
        "X": [[10, 60], [10, 8]],
        "SL": [[32, 59], [34, 10]],
        "TE": [[66, 60], [64, 10]],
        "Z": [[90, 60], [90, 8]],
        "HB": [[46, 72], [52, 66]],
    },
    "PA Boot Over": {
        "TE": [[64, 60], [64, 42], [48, 38]],
        "SL": [[32, 59], [32, 55], [10, 53]],
        "X": [[12, 60], [12, 54], [54, 50]],
        "Z": [[90, 60], [90, 40], [85, 44]],
        "HB": [[46, 72], [30, 66]],
    },
    "Deep Post": {
        "X": [[12, 60], [12, 40], [34, 20]],
        "Z": [[88, 60], [88, 40], [66, 20]],
        "SL": [[32, 59], [32, 48], [32, 50]],
        "TE": [[64, 60], [64, 54], [84, 52]],
        "HB": [[46, 72], [54, 66]],
    },
    "Quick Slants": {
        "X": [[12, 60], [12, 55], [26, 50]],
        "SL": [[32, 59], [32, 55], [46, 50]],
        "Z": [[88, 60], [88, 55], [74, 50]],
        "TE": [[64, 60], [86, 58]],
        "HB": [[46, 72], [52, 68]],
    },
    "Smash Concept": {
        "Z": [[88, 60], [88, 42], [72, 34]],
        "SL": [[70, 59], [70, 54], [90, 52]],
        "X": [[12, 60], [12, 55], [26, 50]],
        "TE": [[40, 60], [40, 48], [40, 52]],
        "HB": [[46, 72], [52, 68]],
    },
    "PA Crossers": {
        "X": [[10, 60], [10, 44], [66, 42]],
        "SL": [[32, 59], [32, 54], [72, 51]],
        "TE": [[64, 60], [64, 57], [88, 55]],
        "Z": [[90, 60], [90, 36], [85, 40]],
        "HB": [[46, 72], [46, 66], [58, 64]],
    },
}

# Preserve receiver order per play (dicts keep insertion order).
TEMPLATE_ROUTES: dict[str, list[RouteSpec]] = {
    name: [RouteSpec(receiver=rec, points=pts) for rec, pts in routes.items()]
    for name, routes in _RAW.items()
}


def routes_for(play_name: str) -> Optional[list[RouteSpec]]:
    """Return curated routes for a template play, or None if none are authored."""
    routes = TEMPLATE_ROUTES.get(play_name)
    # Return copies so callers can't mutate the shared library.
    return [r.model_copy(deep=True) for r in routes] if routes else None

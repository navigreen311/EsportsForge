"""Arsenal weapon → AnimaForge animation spec builder.

Pure function: takes a `SecretWeapon` row and returns the JSON-serializable
spec sent to AnimaForge `/api/v1/render`. Coverage matches blueprint
Section 2 — all 11 titles get bespoke template/style/duration combos.

`cfb-26` reuses the `madden-26` template (per contract §9). Any unknown
title falls back to the madden template.

Owner: Agent #4 (arsenal-backend).
"""

from __future__ import annotations

from typing import Any


# Brand colors — keep in sync with blueprint Section 2.
_HIGHLIGHT_COLOR = "#4ADE80"     # EsportsForge green
_BRAND_COLOR = "#0A0C10"         # EsportsForge dark
_LOGO = "esportsforge"


def _common(weapon: Any) -> dict[str, Any]:
    """Fields every spec carries regardless of title."""
    return {
        "weaponId": getattr(weapon, "id", None),
        "playName": getattr(weapon, "play_name", None),
        "formation": getattr(weapon, "formation", None),
        "executionPath": getattr(weapon, "instructions", []) or [],
        "setupMotions": getattr(weapon, "setup_steps", []) or [],
        "voiceoverText": getattr(weapon, "description", None),
        "highlightColor": _HIGHLIGHT_COLOR,
        "brandColor": _BRAND_COLOR,
        "logo": _LOGO,
    }


def _madden_spec(weapon: Any) -> dict[str, Any]:
    """Football play diagram — top-down field, animated routes, gap highlights."""
    return {
        **_common(weapon),
        "template": "football-play-diagram",
        "duration": 12,
        "style": {
            "background": "field-top-down",
            "playerIcons": "circles-with-numbers",
            "routeLines": "animated-arrows",
            "gapHighlight": True,
        },
    }


def _nba_spec(weapon: Any) -> dict[str, Any]:
    """Basketball play diagram — top-down court."""
    return {
        **_common(weapon),
        "template": "basketball-play-diagram",
        "duration": 10,
        "style": {
            "background": "court-top-down",
            "playerIcons": "circles-with-positions",
            "screenPath": True,
            "cutLines": "animated-arrows",
        },
    }


def _eafc_spec(weapon: Any) -> dict[str, Any]:
    """Soccer play diagram — top-down pitch."""
    return {
        **_common(weapon),
        "template": "soccer-play-diagram",
        "duration": 12,
        "style": {
            "background": "pitch-top-down",
            "playerIcons": "circles",
            "runLines": "animated-arrows",
            "ballPath": "dotted-line",
        },
    }


def _mlb_spec(weapon: Any) -> dict[str, Any]:
    """Baseball — pitcher side-on + top-down for fielding (blueprint Section 2)."""
    return {
        **_common(weapon),
        "template": "baseball-play-diagram",
        "duration": 9,
        "style": {
            "background": "pitcher-side-view",
            "secondaryView": "field-top-down",
            "ballTrajectory": "animated-arc",
            "zoneHighlight": True,
            "batterStance": "highlighted",
        },
    }


def _warzone_spec(weapon: Any) -> dict[str, Any]:
    """FPS tactical diagram — squad rotation across map."""
    return {
        **_common(weapon),
        "template": "fps-tactical-diagram",
        "duration": 14,
        "style": {
            "background": "map-top-down",
            "squadMarkers": True,
            "rotationArrows": "animated",
            "coverPositions": "highlighted-zones",
        },
    }


def _fortnite_spec(weapon: Any) -> dict[str, Any]:
    """Fortnite build/edit diagram — isometric build sequence."""
    return {
        **_common(weapon),
        "template": "fortnite-build-diagram",
        "duration": 11,
        "style": {
            "background": "isometric-build",
            "buildSequence": "step-by-step",
            "editPath": "animated-highlight",
        },
    }


def _ufc_spec(weapon: Any) -> dict[str, Any]:
    """UFC combo — side view octagon, animated strike arcs."""
    return {
        **_common(weapon),
        "template": "fighting-combo-diagram",
        "duration": 9,
        "style": {
            "background": "side-view-octagon",
            "strikePaths": "animated-arcs",
            "timingWindows": "highlighted-frames",
        },
    }


def _pga_spec(weapon: Any) -> dict[str, Any]:
    """Golf shot diagram — side fairway + green overhead."""
    return {
        **_common(weapon),
        "template": "golf-shot-diagram",
        "duration": 10,
        "style": {
            "background": "side-view-fairway",
            "ballFlight": "animated-arc",
            "windLine": "arrow",
            "landingZone": "highlighted-circle",
        },
    }


def _undisputed_spec(weapon: Any) -> dict[str, Any]:
    """Boxing combo — side view ring, punch arcs, footwork dots."""
    return {
        **_common(weapon),
        "template": "boxing-combo-diagram",
        "duration": 9,
        "style": {
            "background": "side-view-ring",
            "punchPaths": "animated-arcs",
            "footworkPattern": "dotted-path",
        },
    }


def _video_poker_spec(weapon: Any) -> dict[str, Any]:
    """Video poker hold diagram — table top-down, card highlights."""
    return {
        **_common(weapon),
        "template": "card-hold-diagram",
        "duration": 7,
        "style": {
            "background": "table-top-down",
            "cardHighlight": "animated-border",
            "holdIndicator": "checkmark-animation",
        },
    }


# Title → builder dispatch. cfb-26 reuses madden per contract §9.
_BUILDERS = {
    "madden-26": _madden_spec,
    "cfb-26": _madden_spec,
    "nba-2k26": _nba_spec,
    "eafc-26": _eafc_spec,
    "mlb-26": _mlb_spec,
    "warzone": _warzone_spec,
    "fortnite": _fortnite_spec,
    "ufc-5": _ufc_spec,
    "pga-2k25": _pga_spec,
    "undisputed": _undisputed_spec,
    "video-poker": _video_poker_spec,
}


def build_weapon_animation_spec(weapon: Any) -> dict[str, Any]:
    """Build an AnimaForge animation spec for a Secret Weapon.

    Args:
        weapon: A `SecretWeapon` row (or any object exposing `title_id`,
            `play_name`, `formation`, `instructions`, `setup_steps`, and
            `description`).

    Returns:
        A JSON-serializable dict ready to pass as the `spec` argument to
        `AnimaForgeService.request_render`. Falls back to the madden-26
        template for unknown titles.
    """
    title_id = getattr(weapon, "title_id", None) or "madden-26"
    builder = _BUILDERS.get(title_id, _madden_spec)
    return builder(weapon)

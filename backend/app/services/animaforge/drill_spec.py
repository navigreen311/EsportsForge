"""Drill demonstration animation spec builder.

Pure function module — given a (title_id, drill_type) pair returns the
animation spec dict that AnimaForge consumes, or ``None`` when no spec
is defined for that combination (caller falls back to text-only mode).

Spec table is verbatim from blueprint Section 3 (with the "Add remaining
titles..." section filled out for the full 11-title coverage).

Drill demos are SHARED across users (cached by ``f"{title_id}:{drill_type}"``
on the AnimaForgeJob row, with ``user_id="system"``).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# ---------------------------------------------------------------------------
# Spec table — full 11-title coverage (blueprint Section 3)
# ---------------------------------------------------------------------------
#
# Drill type slugs (kebab-case) are the canonical IDs the frontend sends.
# Mapping from blueprint table headings:
#   "Pre-Snap Read"        → "pre-snap-reads"
#   "Blitz Timing"         → "blitz-timing"
#   "Red Zone Execution"   → "red-zone-execution"
#   "On-Ball Defense"      → "on-ball-defense"
#   "PNR Coverage"         → "pnr-coverage"
#   "Shot Timing"          → "shot-timing"
#   "Jockey Technique"     → "jockey-timing"   (frontend slug)
#   "Skill Move"           → "skill-move"
#   "Pitch Sequence"       → "pitch-sequence"
#   "Movement Tech"        → "movement-tech"
#   "Edit Speed"           → "edit-speed"
#   "Takedown Defense"     → "takedown-defense"
#   "Shot Shape"           → "shot-shape"
#   "Parry Timing"         → "parry-timing"
#   "Optimal Hold"         → "optimal-hold"

DRILL_ANIMATION_SPECS: dict[str, dict[str, dict[str, Any]]] = {
    # ─── Madden 26 ──────────────────────────────────────────────────────
    "madden-26": {
        "pre-snap-reads": {
            "template": "football-pre-snap-demo",
            "sequence": [
                {"step": 1, "action": "show-defense-alignment",
                 "duration": 2, "highlight": "safeties"},
                {"step": 2, "action": "reveal-coverage-shell",
                 "duration": 2, "highlight": "coverage-zone"},
                {"step": 3, "action": "show-correct-hot-route",
                 "duration": 2, "highlight": "route-arrow"},
                {"step": 4, "action": "show-snap-timing",
                 "duration": 2, "highlight": "snap-count"},
                {"step": 5, "action": "show-result",
                 "duration": 2, "highlight": "completion-marker"},
            ],
            "voiceover": (
                "Read the safeties. Identify the shell. "
                "Make the hot route. Then snap."
            ),
            "duration": 10,
            "style": {
                "background": "field-top-down",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
        "blitz-timing": {
            "template": "football-blitz-demo",
            "sequence": [
                {"step": 1, "action": "show-blitz-setup", "duration": 2},
                {"step": 2, "action": "animate-snap", "duration": 1},
                {"step": 3, "action": "show-blitz-path", "duration": 2},
                {"step": 4, "action": "show-qb-contact-point", "duration": 2},
            ],
            "voiceover": (
                "Time the snap. Attack the gap. "
                "Hit the QB before he sets."
            ),
            "duration": 8,
            "style": {
                "background": "field-top-down",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
        "red-zone-execution": {
            "template": "football-red-zone-demo",
            "sequence": [
                {"step": 1, "action": "show-formation-set",
                 "duration": 2, "highlight": "compressed-spacing"},
                {"step": 2, "action": "animate-snap", "duration": 1},
                {"step": 3, "action": "show-route-breaks",
                 "duration": 3, "highlight": "break-points"},
                {"step": 4, "action": "show-catch-point",
                 "duration": 2, "highlight": "completion-marker"},
            ],
            "voiceover": (
                "Tight space. Sharp breaks. "
                "Throw to the catch point — not the receiver."
            ),
            "duration": 8,
            "style": {
                "background": "field-top-down-redzone",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
    },

    # ─── NBA 2K26 ───────────────────────────────────────────────────────
    "nba-2k26": {
        "on-ball-defense": {
            "template": "basketball-defense-demo",
            "sequence": [
                {"step": 1, "action": "show-defensive-stance", "duration": 2},
                {"step": 2, "action": "mirror-dribble-movement", "duration": 3},
                {"step": 3, "action": "show-closeout-footwork", "duration": 2},
                {"step": 4, "action": "contest-shot", "duration": 2},
            ],
            "voiceover": (
                "Stay low. Mirror the ball. "
                "Chop on the closeout. Contest high."
            ),
            "duration": 10,
            "style": {
                "background": "court-top-down",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
        "pnr-coverage": {
            "template": "basketball-pnr-demo",
            "sequence": [
                {"step": 1, "action": "show-screen-set",
                 "duration": 2, "highlight": "screener"},
                {"step": 2, "action": "show-hedge-position",
                 "duration": 2, "highlight": "big-man-hedge"},
                {"step": 3, "action": "show-recovery-path",
                 "duration": 2, "highlight": "recovery-arrow"},
                {"step": 4, "action": "show-switch-timing",
                 "duration": 2, "highlight": "switch-trigger"},
            ],
            "voiceover": (
                "Hedge hard. Recover quick. "
                "Switch on the call — not before."
            ),
            "duration": 8,
            "style": {
                "background": "court-top-down",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
        "shot-timing": {
            "template": "basketball-shot-meter-demo",
            "sequence": [
                {"step": 1, "action": "show-shot-meter", "duration": 2},
                {"step": 2, "action": "highlight-green-window", "duration": 2},
                {"step": 3, "action": "animate-release-timing", "duration": 2},
                {"step": 4, "action": "show-result", "duration": 2},
            ],
            "voiceover": (
                "Watch the meter. Release in the green. "
                "Do not rush. Time it."
            ),
            "duration": 8,
            "style": {
                "background": "court-side-view",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
    },

    # ─── EA FC 26 ───────────────────────────────────────────────────────
    "eafc-26": {
        # Blueprint table heading "Jockey Technique" maps to slug
        # "jockey-timing" — this is the canonical slug the drill catalog uses.
        "jockey-timing": {
            "template": "soccer-defense-demo",
            "sequence": [
                {"step": 1, "action": "show-jockey-stance", "duration": 2},
                {"step": 2, "action": "lateral-movement", "duration": 3},
                {"step": 3, "action": "force-to-sideline", "duration": 2},
                {"step": 4, "action": "clean-tackle", "duration": 2},
            ],
            "voiceover": (
                "Hold L2. Stay on your feet. "
                "Force them wide. Then tackle."
            ),
            "duration": 10,
            "style": {
                "background": "pitch-top-down",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
        "skill-move": {
            "template": "soccer-skill-move-demo",
            "sequence": [
                {"step": 1, "action": "show-input-sequence",
                 "duration": 2, "highlight": "stick-icons"},
                {"step": 2, "action": "show-body-movement",
                 "duration": 3, "highlight": "player-silhouette"},
                {"step": 3, "action": "show-direction-change",
                 "duration": 2, "highlight": "movement-arrow"},
                {"step": 4, "action": "show-result",
                 "duration": 2, "highlight": "space-created"},
            ],
            "voiceover": (
                "Flick the stick. Sell the body. "
                "Burst the other direction."
            ),
            "duration": 9,
            "style": {
                "background": "pitch-top-down",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
    },

    # ─── MLB The Show 26 ────────────────────────────────────────────────
    "mlb-26": {
        "pitch-sequence": {
            "template": "baseball-pitch-sequence-demo",
            "sequence": [
                {"step": 1, "action": "show-first-pitch",
                 "duration": 2, "highlight": "zone-edge"},
                {"step": 2, "action": "show-second-pitch",
                 "duration": 2, "highlight": "off-zone-chase"},
                {"step": 3, "action": "show-third-pitch",
                 "duration": 2, "highlight": "back-foot-bury"},
                {"step": 4, "action": "show-putaway-pitch",
                 "duration": 2, "highlight": "called-strike"},
            ],
            "voiceover": (
                "Set up the zone. Pull them off it. "
                "Then put them away."
            ),
            "duration": 8,
            "style": {
                "background": "pitcher-side-view",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
    },

    # ─── Warzone ────────────────────────────────────────────────────────
    "warzone": {
        "movement-tech": {
            "template": "fps-movement-demo",
            "sequence": [
                {"step": 1, "action": "show-cover-position", "duration": 2},
                {"step": 2, "action": "slide-cancel-path", "duration": 3},
                {"step": 3, "action": "peek-return", "duration": 2},
                {"step": 4, "action": "next-cover", "duration": 2},
            ],
            "voiceover": (
                "Use cover. Slide cancel to close distance. "
                "Peek and return. Never stand still."
            ),
            "duration": 10,
            "style": {
                "background": "map-top-down",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
    },

    # ─── Fortnite ───────────────────────────────────────────────────────
    "fortnite": {
        "edit-speed": {
            "template": "fortnite-edit-demo",
            "sequence": [
                {"step": 1, "action": "show-build-state",
                 "duration": 2, "highlight": "starting-build"},
                {"step": 2, "action": "highlight-edit-tiles",
                 "duration": 2, "highlight": "edit-tiles"},
                {"step": 3, "action": "show-decision-point",
                 "duration": 2, "highlight": "peek-window"},
                {"step": 4, "action": "show-reset-position",
                 "duration": 2, "highlight": "reset-tiles"},
            ],
            "voiceover": (
                "Plan the edit. Peek the kill. "
                "Reset before they shoot."
            ),
            "duration": 8,
            "style": {
                "background": "isometric-build",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
    },

    # ─── UFC 5 ──────────────────────────────────────────────────────────
    "ufc-5": {
        "takedown-defense": {
            "template": "fighting-sprawl-demo",
            "sequence": [
                {"step": 1, "action": "show-shoot-telegraph", "duration": 2},
                {"step": 2, "action": "sprawl-timing", "duration": 2},
                {"step": 3, "action": "hip-position", "duration": 2},
                {"step": 4, "action": "return-to-standing", "duration": 2},
            ],
            "voiceover": (
                "See the shoot. Sprawl instantly. "
                "Hips back. Weight forward."
            ),
            "duration": 9,
            "style": {
                "background": "side-view-octagon",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
    },

    # ─── PGA TOUR 2K25 ──────────────────────────────────────────────────
    "pga-2k25": {
        "shot-shape": {
            "template": "golf-shot-shape-demo",
            "sequence": [
                {"step": 1, "action": "show-club-path",
                 "duration": 2, "highlight": "swing-arc"},
                {"step": 2, "action": "show-face-angle",
                 "duration": 2, "highlight": "club-face"},
                {"step": 3, "action": "show-ball-flight",
                 "duration": 3, "highlight": "flight-curve"},
                {"step": 4, "action": "show-landing-zone",
                 "duration": 2, "highlight": "landing-circle"},
            ],
            "voiceover": (
                "Path in. Face open. "
                "Watch the ball curve. Land soft."
            ),
            "duration": 9,
            "style": {
                "background": "side-view-fairway",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
    },

    # ─── Undisputed ─────────────────────────────────────────────────────
    "undisputed": {
        "parry-timing": {
            "template": "boxing-parry-demo",
            "sequence": [
                {"step": 1, "action": "show-punch-recognition",
                 "duration": 2, "highlight": "incoming-punch"},
                {"step": 2, "action": "show-parry-input",
                 "duration": 2, "highlight": "parry-frame"},
                {"step": 3, "action": "show-counter-window",
                 "duration": 2, "highlight": "counter-opening"},
                {"step": 4, "action": "show-counter-punch",
                 "duration": 2, "highlight": "counter-strike"},
            ],
            "voiceover": (
                "Read the punch. Parry on frame. "
                "Counter into the opening."
            ),
            "duration": 8,
            "style": {
                "background": "side-view-ring",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
    },

    # ─── Video Poker ────────────────────────────────────────────────────
    "video-poker": {
        "optimal-hold": {
            "template": "card-hold-demo",
            "sequence": [
                {"step": 1, "action": "show-dealt-hand",
                 "duration": 2, "highlight": "five-cards"},
                {"step": 2, "action": "highlight-hold-decision",
                 "duration": 2, "highlight": "hold-cards"},
                {"step": 3, "action": "show-expected-value",
                 "duration": 2, "highlight": "ev-display"},
                {"step": 4, "action": "show-draw-result",
                 "duration": 1, "highlight": "draw-cards"},
            ],
            "voiceover": (
                "See the hand. Hold the EV play. "
                "Draw what's left."
            ),
            "duration": 7,
            "style": {
                "background": "table-top-down",
                "highlightColor": "#4ADE80",
                "brandColor": "#0A0C10",
            },
        },
    },
}


# CFB 26 reuses Madden 26's spec table — same drill types, same animations.
DRILL_ANIMATION_SPECS["cfb-26"] = deepcopy(DRILL_ANIMATION_SPECS["madden-26"])


def build_drill_animation_spec(title_id: str, drill_type: str) -> dict | None:
    """Return the AnimaForge animation spec for a (title, drill) combo.

    Returns ``None`` when no spec exists for the requested combination —
    callers should treat this as "no animation available" and fall back
    to text-only mode silently (per blueprint graceful-degradation rule).

    The returned dict is a deep copy — callers may mutate freely without
    polluting the spec table.
    """
    title_specs = DRILL_ANIMATION_SPECS.get(title_id)
    if title_specs is None:
        return None
    spec = title_specs.get(drill_type)
    if spec is None:
        return None
    return deepcopy(spec)


__all__ = ["DRILL_ANIMATION_SPECS", "build_drill_animation_spec"]

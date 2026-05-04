"""DefenseAI helpers — Claude prompts shared by /defensive-gameplan."""

from __future__ import annotations

import json
from typing import Any

from app.services.arsenal_ai import call_claude, parse_json_object  # noqa: F401


# ---------------------------------------------------------------------------
# Per-title defensive context
# ---------------------------------------------------------------------------

TITLE_DEFENSE_CONTEXT: dict[str, dict[str, Any]] = {
    "madden-26": {
        "label": "Defense",
        "schemes": [
            "Cover 1", "Cover 2", "Cover 2 Man", "Cover 3", "Cover 3 Sky",
            "Cover 3 Buzz", "Cover 4", "Cover 4 Quarters", "Cover 6",
            "Man Press", "Man Bail", "Cover 0 Blitz",
        ],
        "blitz_packages": [
            "A-Gap Blitz", "Edge Blitz", "DB Blitz", "Zero Blitz",
            "Overload Blitz", "Fire Zone",
        ],
        "formations": [
            "4-3 Even", "4-3 Over", "3-4 Odd", "Nickel 3-3-5",
            "Dime 2-3-6", "Dollar", "Goal Line", "Prevent",
        ],
        "concepts": [
            "User Coverage", "QB Spy", "Zone Drop", "Hook Curl",
            "Robber Coverage", "QB Contain", "Pass Rush Moves",
            "Shade Coverage", "Coverage Rotation", "Safety Help",
        ],
    },
    "cfb-26": {
        "label": "Defense",
        "schemes": [
            "Cover 1", "Cover 2", "Cover 3", "Cover 4", "Tampa 2",
            "Quarters", "Man Press", "Cover 0",
        ],
        "formations": ["4-2-5", "3-3-5", "4-3", "3-4", "Nickel", "Dime", "Goal Line"],
        "concepts": [
            "Spy Assignment", "Zone Coverage", "Blitz Packages",
            "Option Defense", "RPO Defense", "Contain Rush",
        ],
    },
    "nba-2k26": {
        "label": "Defense",
        "schemes": [
            "Man-to-Man", "Zone 2-3", "Zone 3-2", "Zone 1-3-1",
            "Switching Man", "Drop Coverage", "Hedge Hard", "Ice PNR", "Show Hard",
        ],
        "concepts": [
            "Help Defense", "On-Ball Defense", "PNR Coverage", "Post Defense",
            "Closeout Technique", "Block Timing", "Steal Timing", "Body Up",
            "Anticipate Pass", "Transition Defense",
        ],
    },
    "eafc-26": {
        "label": "Defense",
        "schemes": [
            "Deep Block", "Medium Block", "High Press", "Counter Press",
            "Back 5", "Offside Trap", "Balanced", "Ultra Defensive",
        ],
        "concepts": [
            "Jockeying", "Tackle Timing", "Interception Timing",
            "Goalkeeper Control", "Defensive Width", "Marking",
            "Press Trigger", "Contain", "Positioning Shape", "Set Piece Defense",
        ],
    },
    "mlb-26": {
        "label": "Pitching & Fielding",
        "pitching": [
            "Sequence Building", "Count Management", "Zone Work",
            "Chase Pitches", "Strikeout Combos", "Weak Contact Induction",
        ],
        "fielding": [
            "Shift Strategy", "Outfield Positioning", "Infield Depth",
            "Double Play Setup", "Pick Off Moves", "Pitch Out Timing",
        ],
    },
    "warzone": {
        "label": "Defensive Tactics",
        "concepts": [
            "Hold Position", "Defensive Rotation", "Zone Edge Defense",
            "Building Defense", "Ambush Setup", "Intel Gathering",
            "Crossfire Coverage", "Third Party Defense",
        ],
    },
    "fortnite": {
        "label": "Defensive Building",
        "concepts": [
            "Box Defense", "Layer Building", "Cone Defense", "Edit Defense",
            "High Ground Defense", "Anti-Push", "Trap Placement",
            "Material Conservation",
        ],
    },
    "ufc-5": {
        "label": "Defense & Grappling",
        "concepts": [
            "Strike Defense", "Takedown Defense", "Submission Defense",
            "Clinch Defense", "Counter Striking", "Footwork Defense",
            "Guard Work", "Wall Defense",
        ],
    },
    "pga-2k25": {
        "label": "Course Management",
        "concepts": [
            "Lay Up Strategy", "Hazard Avoidance", "Conservative Line",
            "Bogey Management", "Wind Defense", "Rough Avoidance",
            "Safe Landing Zones", "Pressure Management",
        ],
    },
    "undisputed": {
        "label": "Defense",
        "concepts": [
            "Head Movement", "Shoulder Roll", "Parry Timing", "Block Timing",
            "Clinch Defense", "Footwork", "Counter Timing", "Guard Management",
        ],
    },
    "video-poker": {
        "label": "Risk Management",
        "concepts": [
            "Bankroll Protection", "Session Limits", "Variance Management",
            "Loss Limit Discipline", "Optimal Hold Strategy", "Paytable Selection",
        ],
    },
}


def build_defensive_gameplan_system(
    title_id: str,
    opponent: dict[str, Any] | None,
    defensive_priorities: list[dict[str, Any]],
) -> str:
    """System prompt for /defensive-gameplan."""
    ctx = TITLE_DEFENSE_CONTEXT.get(title_id, {})
    return f"""\
You are DefenseAI for EsportsForge.

TITLE: {title_id}
DEFENSE LABEL: {ctx.get('label', 'Defense')}
AVAILABLE SCHEMES: {json.dumps(ctx.get('schemes', ctx.get('concepts', [])))}
{('AVAILABLE BLITZ PACKAGES: ' + json.dumps(ctx.get('blitz_packages', []))) if 'blitz_packages' in ctx else ''}
{('FORMATIONS: ' + json.dumps(ctx.get('formations', []))) if 'formations' in ctx else ''}

OPPONENT: {json.dumps(opponent) if opponent else 'no opponent context provided'}
PLAYER DEFENSIVE WEAKNESSES: {json.dumps(defensive_priorities)}

Generate a complete defensive gameplan that:
1. Counters the opponent's offensive tendencies (if provided)
2. Fits the player's available schemes for this title
3. Has situational adjustments
4. Includes coverage / scheme checks

Return ONLY JSON (no markdown, no preamble):
{{
  "primary_scheme": {{
    "name": str,
    "description": str,
    "when_to_use": str,
    "coverage_shell": str|null,
    "blitz_rate": number,
    "confidence": number
  }},
  "situational_packages": [{{
    "situation": str,
    "scheme": str,
    "adjustment": str,
    "confidence": number,
    "reasoning": str
  }}],
  "opponent_counters": [{{
    "opponent_tendency": str,
    "your_adjustment": str,
    "confidence": number,
    "evidence": str
  }}],
  "pre_snap_keys": [str],
  "adjustment_triggers": [{{
    "trigger": str,
    "adjustment": str,
    "reason": str
  }}],
  "weaknesses": [str],
  "practice_points": [str]
}}

Limit situational_packages to 5 entries, opponent_counters to 5 entries.
"""

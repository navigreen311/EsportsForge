"""Fix scoring — generates and evaluates fixes for player weaknesses."""

from __future__ import annotations

import logging
from uuid import uuid4

from app.schemas.impact_rank import (
    Fix,
    FixScore,
    Weakness,
    WeaknessCategory,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fix templates per weakness category
# ---------------------------------------------------------------------------

_FIX_TEMPLATES: dict[WeaknessCategory, list[dict]] = {
    WeaknessCategory.MECHANICAL: [
        {
            "label": "Drill repetition",
            "description": "Targeted muscle-memory drill in practice mode.",
            "drill": "Run the specific mechanic 50 times in practice before each session.",
            "base_lift": 0.08,
            "base_hours": 5.0,
        },
        {
            "label": "Slow-motion rehearsal",
            "description": "Execute at half speed until clean, then ramp up.",
            "drill": "Use training mode with slowed game speed for 15-min blocks.",
            "base_lift": 0.05,
            "base_hours": 3.0,
        },
    ],
    WeaknessCategory.DECISION: [
        {
            "label": "Film study",
            "description": "Review replays focusing on decision points.",
            "drill": "Watch 3 losses, pause at each key decision, write the better option.",
            "base_lift": 0.12,
            "base_hours": 4.0,
        },
        {
            "label": "Situational scripting",
            "description": "Pre-plan decisions for common game states.",
            "drill": "Create an if-then playsheet for your top 10 problem situations.",
            "base_lift": 0.10,
            "base_hours": 3.0,
        },
    ],
    WeaknessCategory.KNOWLEDGE: [
        {
            "label": "Meta research",
            "description": "Study current meta counters and matchup data.",
            "drill": "Spend 30 min reviewing top-player strategies and counter-picks.",
            "base_lift": 0.06,
            "base_hours": 2.0,
        },
        {
            "label": "Scheme deep-dive",
            "description": "Master the mechanics of the scheme causing trouble.",
            "drill": "Lab the specific scheme in practice for 20 min daily.",
            "base_lift": 0.07,
            "base_hours": 3.0,
        },
    ],
    WeaknessCategory.MENTAL: [
        {
            "label": "Tilt protocol",
            "description": "Implement a structured break/reset routine.",
            "drill": "After 2 consecutive losses, take a 5-min break. Breathe. Reset.",
            "base_lift": 0.10,
            "base_hours": 1.0,
        },
        {
            "label": "Process focus",
            "description": "Shift focus from outcome to execution quality.",
            "drill": "Rate your decision quality 1-10 each game regardless of W/L.",
            "base_lift": 0.08,
            "base_hours": 2.0,
        },
    ],
    WeaknessCategory.TACTICAL: [
        {
            "label": "Positional drilling",
            "description": "Practice specific tactical setups in isolation.",
            "drill": "Run the tactical scenario 20 times in practice mode.",
            "base_lift": 0.09,
            "base_hours": 4.0,
        },
        {
            "label": "Counter-tactic study",
            "description": "Learn specific counters to the tactics exploiting you.",
            "drill": "Identify the top 3 tactics beating you and lab 2 counters each.",
            "base_lift": 0.07,
            "base_hours": 3.0,
        },
    ],
}


def generate_fixes(weakness: Weakness) -> list[Fix]:
    """Generate candidate fixes for a weakness from templates.

    In production this would also call an LLM for personalized fix generation.
    Current implementation uses category-based fix templates.
    """
    templates = _FIX_TEMPLATES.get(weakness.category, _FIX_TEMPLATES[WeaknessCategory.DECISION])
    fixes: list[Fix] = []

    for tmpl in templates:
        fix = Fix(
            id=uuid4(),
            weakness_id=weakness.id,
            label=tmpl["label"],
            description=tmpl["description"],
            drill=tmpl["drill"],
        )
        fixes.append(fix)

    logger.info(
        "Generated %d fixes for weakness=%s category=%s",
        len(fixes),
        weakness.label,
        weakness.category.value,
    )
    return fixes


def score_fix_roi(fix: Fix, player_profile: dict | None = None) -> FixScore:
    """Score a fix by ROI: expected_lift / time_to_master, adjusted by transfer rate.

    Args:
        fix: The fix to score.
        player_profile: Optional dict with ``skill_level`` (0-1),
            ``practice_hours_weekly``, ``learning_speed`` (0-1) keys.
    """
    player_profile = player_profile or {}

    # Look up base values from template
    category_templates = {}
    for cat_templates in _FIX_TEMPLATES.values():
        for tmpl in cat_templates:
            category_templates[tmpl["label"]] = tmpl

    tmpl = category_templates.get(fix.label, {"base_lift": 0.05, "base_hours": 4.0})
    base_lift = tmpl["base_lift"]
    base_hours = tmpl["base_hours"]

    # Adjust by player profile
    skill_level = player_profile.get("skill_level", 0.5)
    learning_speed = player_profile.get("learning_speed", 0.5)

    # Higher skill = diminishing returns on basic fixes, but better transfer
    expected_lift = base_lift * (1.0 - skill_level * 0.3)
    time_to_master = base_hours * (1.5 - learning_speed)

    # Transfer rate: how likely the player executes under pressure
    base_transfer = 0.6
    execution_transfer_rate = min(base_transfer + (skill_level * 0.3), 1.0)

    return FixScore(
        expected_lift=round(min(max(expected_lift, 0.01), 1.0), 4),
        time_to_master_hours=round(max(time_to_master, 0.5), 2),
        execution_transfer_rate=round(min(max(execution_transfer_rate, 0.1), 1.0), 4),
    )


def check_execution_feasibility(fix: Fix, player_twin: dict | None = None) -> float:
    """Estimate whether the player can realistically execute this fix.

    Returns a feasibility score 0-1.  In production this queries the PlayerTwin
    backbone service for detailed capability data.

    Args:
        fix: The fix to evaluate.
        player_twin: Optional dict with ``mechanical_ceiling`` (0-1),
            ``mental_resilience`` (0-1), ``time_available_hours`` keys.
    """
    player_twin = player_twin or {}

    mechanical_ceiling = player_twin.get("mechanical_ceiling", 0.5)
    mental_resilience = player_twin.get("mental_resilience", 0.5)
    time_available = player_twin.get("time_available_hours", 5.0)

    # Check if fix requires more time than player has
    fix_score = fix.fix_score
    if fix_score and fix_score.time_to_master_hours > time_available * 2:
        time_penalty = 0.5
    else:
        time_penalty = 1.0

    feasibility = (
        (mechanical_ceiling * 0.4)
        + (mental_resilience * 0.3)
        + (0.3 * time_penalty)
    )

    return round(min(max(feasibility, 0.0), 1.0), 4)

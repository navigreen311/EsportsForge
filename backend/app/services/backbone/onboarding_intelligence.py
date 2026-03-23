"""Onboarding Intelligence — guided first-3-sessions flow.

Walks a new user through three calibration sessions, extracts early
behavioral signals, and bootstraps a PlayerTwin profile with an initial
gameplan.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from app.schemas.film import (
    FirstGameplan,
    OnboardingPhase,
    OnboardingProfile,
    OnboardingStep,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory stores (replaced by DB in production)
# ---------------------------------------------------------------------------

# (user_id, title) -> OnboardingProfile
_profiles: dict[tuple[str, str], OnboardingProfile] = {}
# user_id -> title -> [session_data dicts]
_session_data: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
    lambda: defaultdict(list)
)
# user_id -> title -> FirstGameplan
_gameplans: dict[tuple[str, str], FirstGameplan] = {}


def reset_store() -> None:
    """Clear all in-memory state (for testing)."""
    _profiles.clear()
    _session_data.clear()
    _gameplans.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _key(user_id: str, title: str) -> tuple[str, str]:
    return (user_id, title)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def start_onboarding(user_id: str, title: str) -> OnboardingProfile:
    """Begin the onboarding flow for a new user + title pair."""
    key = _key(user_id, title)
    if key in _profiles and _profiles[key].current_phase == OnboardingPhase.COMPLETED:
        raise ValueError(
            f"Onboarding already completed for user {user_id} in {title}"
        )

    profile = OnboardingProfile(
        user_id=user_id,
        title=title,
        current_phase=OnboardingPhase.SESSION_1,
        steps=[],
        started_at=_now(),
    )
    _profiles[key] = profile
    logger.info("Started onboarding for user %s in %s", user_id, title)
    return profile


def process_first_session(
    user_id: str, session_data: dict[str, Any]
) -> OnboardingProfile:
    """Learn from the user's first calibration session.

    Extracts: basic playstyle tendency, preferred game mode, initial
    comfort zones.
    """
    title = session_data.get("title", "unknown")
    key = _key(user_id, title)
    profile = _profiles.get(key)
    if profile is None:
        raise ValueError(f"No onboarding started for user {user_id} in {title}")
    if profile.current_phase != OnboardingPhase.SESSION_1:
        raise ValueError(
            f"Expected phase SESSION_1, got {profile.current_phase}"
        )

    _session_data[user_id][title].append(session_data)

    # Phase 1 heuristic: derive early playstyle from session stats
    insights = _extract_session1_insights(session_data)

    step = OnboardingStep(
        step_number=1,
        phase=OnboardingPhase.SESSION_1,
        completed=True,
        insights=insights,
        completed_at=_now(),
    )
    profile.steps.append(step)
    profile.preliminary_playstyle = insights.get("playstyle_guess", "balanced")
    profile.current_phase = OnboardingPhase.SESSION_2

    logger.info("Processed session 1 for user %s in %s", user_id, title)
    return profile


def process_second_session(
    user_id: str, session_data: dict[str, Any]
) -> OnboardingProfile:
    """Refine understanding from the second session.

    Looks for: consistency vs. session 1, adaptability signals, strength /
    weakness emergence.
    """
    title = session_data.get("title", "unknown")
    key = _key(user_id, title)
    profile = _profiles.get(key)
    if profile is None:
        raise ValueError(f"No onboarding started for user {user_id} in {title}")
    if profile.current_phase != OnboardingPhase.SESSION_2:
        raise ValueError(
            f"Expected phase SESSION_2, got {profile.current_phase}"
        )

    _session_data[user_id][title].append(session_data)

    insights = _extract_session2_insights(user_id, title, session_data)

    step = OnboardingStep(
        step_number=2,
        phase=OnboardingPhase.SESSION_2,
        completed=True,
        insights=insights,
        completed_at=_now(),
    )
    profile.steps.append(step)
    profile.current_phase = OnboardingPhase.SESSION_3

    logger.info("Processed session 2 for user %s in %s", user_id, title)
    return profile


def process_third_session(
    user_id: str, session_data: dict[str, Any]
) -> OnboardingProfile:
    """Finalize onboarding from the third session and bootstrap PlayerTwin.

    After session 3 we have enough data to commit to a preliminary player
    model and generate the first gameplan.
    """
    title = session_data.get("title", "unknown")
    key = _key(user_id, title)
    profile = _profiles.get(key)
    if profile is None:
        raise ValueError(f"No onboarding started for user {user_id} in {title}")
    if profile.current_phase != OnboardingPhase.SESSION_3:
        raise ValueError(
            f"Expected phase SESSION_3, got {profile.current_phase}"
        )

    _session_data[user_id][title].append(session_data)

    insights = _extract_session3_insights(user_id, title, session_data)

    step = OnboardingStep(
        step_number=3,
        phase=OnboardingPhase.SESSION_3,
        completed=True,
        insights=insights,
        completed_at=_now(),
    )
    profile.steps.append(step)
    profile.current_phase = OnboardingPhase.COMPLETED
    profile.completed_at = _now()

    logger.info(
        "Completed onboarding for user %s in %s — ready for PlayerTwin bootstrap",
        user_id, title,
    )
    return profile


def install_first_gameplan(user_id: str, title: str) -> FirstGameplan:
    """Generate and store the initial gameplan after onboarding completes."""
    key = _key(user_id, title)
    profile = _profiles.get(key)
    if profile is None or profile.current_phase != OnboardingPhase.COMPLETED:
        raise ValueError(
            f"Onboarding not yet completed for user {user_id} in {title}"
        )

    sessions = _session_data.get(user_id, {}).get(title, [])
    gameplan = _build_first_gameplan(user_id, title, profile, sessions)
    _gameplans[key] = gameplan

    logger.info("Installed first gameplan for user %s in %s", user_id, title)
    return gameplan


def get_onboarding_progress(user_id: str, title: str | None = None) -> dict[str, Any]:
    """Return progress through onboarding steps.

    If *title* is None, returns progress across all titles.
    """
    results: dict[str, Any] = {}
    for (uid, t), profile in _profiles.items():
        if uid != user_id:
            continue
        if title is not None and t != title:
            continue
        results[t] = {
            "current_phase": profile.current_phase.value,
            "steps_completed": len(profile.steps),
            "total_steps": 3,
            "preliminary_playstyle": profile.preliminary_playstyle,
            "completed": profile.current_phase == OnboardingPhase.COMPLETED,
        }
    return results


# ---------------------------------------------------------------------------
# Internal insight extraction (Phase 1 — rule-based heuristics)
# ---------------------------------------------------------------------------

def _extract_session1_insights(data: dict[str, Any]) -> dict[str, Any]:
    """Derive initial signals from the first session."""
    plays = data.get("plays", [])
    result = data.get("result", "unknown")

    # Rough playstyle detection
    aggressive_count = sum(1 for p in plays if p.get("type") in {"blitz", "deep_pass", "aggressive_run"})
    total = max(len(plays), 1)
    aggression_ratio = aggressive_count / total

    if aggression_ratio > 0.6:
        playstyle = "aggressive"
    elif aggression_ratio < 0.3:
        playstyle = "conservative"
    else:
        playstyle = "balanced"

    return {
        "playstyle_guess": playstyle,
        "aggression_ratio": round(aggression_ratio, 3),
        "total_plays": total,
        "result": result,
    }


def _extract_session2_insights(
    user_id: str, title: str, data: dict[str, Any]
) -> dict[str, Any]:
    """Compare session 2 to session 1 for consistency signals."""
    sessions = _session_data.get(user_id, {}).get(title, [])
    s1_insights = {}
    if sessions:
        s1_insights = _extract_session1_insights(sessions[0])

    s2_insights = _extract_session1_insights(data)

    # Consistency check
    s1_style = s1_insights.get("playstyle_guess", "balanced")
    s2_style = s2_insights.get("playstyle_guess", "balanced")
    consistent = s1_style == s2_style

    return {
        **s2_insights,
        "consistent_with_session_1": consistent,
        "session_1_playstyle": s1_style,
        "adaptability_signal": not consistent,
    }


def _extract_session3_insights(
    user_id: str, title: str, data: dict[str, Any]
) -> dict[str, Any]:
    """Final insight extraction, summarizing across all three sessions."""
    sessions = _session_data.get(user_id, {}).get(title, [])
    all_insights = [_extract_session1_insights(s) for s in sessions]

    playstyles = [i.get("playstyle_guess", "balanced") for i in all_insights]
    # Majority vote
    from collections import Counter
    style_counts = Counter(playstyles)
    dominant_style = style_counts.most_common(1)[0][0] if style_counts else "balanced"

    avg_aggression = (
        sum(i.get("aggression_ratio", 0.5) for i in all_insights) / max(len(all_insights), 1)
    )

    wins = sum(1 for i in all_insights if i.get("result") == "win")

    return {
        "dominant_playstyle": dominant_style,
        "avg_aggression": round(avg_aggression, 3),
        "win_rate": round(wins / max(len(all_insights), 1), 3),
        "sessions_analyzed": len(all_insights),
    }


def _build_first_gameplan(
    user_id: str,
    title: str,
    profile: OnboardingProfile,
    sessions: list[dict[str, Any]],
) -> FirstGameplan:
    """Build the initial gameplan from onboarding data."""
    # Gather final insights
    final_step = profile.steps[-1] if profile.steps else None
    insights = final_step.insights if final_step else {}

    playstyle = insights.get("dominant_playstyle", profile.preliminary_playstyle or "balanced")

    # Strategy mapping
    strategy_map = {
        "aggressive": "High-tempo offense with frequent blitzes on defense",
        "conservative": "Ball-control offense with zone coverage defense",
        "balanced": "Balanced scheme mixing run/pass with situational blitzes",
    }

    focus_map = {
        "aggressive": ["Deep passing routes", "Blitz packages", "Aggressive play-calling"],
        "conservative": ["Clock management", "Zone coverage reads", "Safe ball handling"],
        "balanced": ["Pre-snap reads", "Situational awareness", "Scheme versatility"],
    }

    starter_map = {
        "aggressive": ["PA Deep Shot", "Cover 0 Blitz", "Aggressive Run"],
        "conservative": ["HB Dive", "Cover 3 Sky", "Short Slant"],
        "balanced": ["Inside Zone", "Cover 2 Man", "PA Crosser"],
    }

    confidence = min(0.5 + (len(sessions) * 0.1), 0.8)

    return FirstGameplan(
        user_id=user_id,
        title=title,
        recommended_strategy=strategy_map.get(playstyle, strategy_map["balanced"]),
        focus_areas=focus_map.get(playstyle, focus_map["balanced"]),
        starter_plays=starter_map.get(playstyle, starter_map["balanced"]),
        confidence=round(confidence, 2),
        generated_at=_now(),
    )

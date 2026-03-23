"""PlayerTwin — the core personalization engine.

Digital model of each player that learns real tendencies, execution ceiling,
and panic patterns.  Updated after every game session via LoopAI data.
Per-title profiles: a player may be aggressive in Madden but conservative in 2K.

Orchestrates the IdentityEngine and ExecutionEngine to produce a unified
PlayerTwinProfile.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.schemas.player_twin import (
    BenchmarkComparison,
    CanExecuteResponse,
    ExecutionScore,
    PanicPattern,
    PlayerIdentity,
    PlayerTwinProfile,
    PressureLevel,
    RecommendationInput,
    SessionData,
    TendencyEntry,
    TendencyMap,
)
from app.services.backbone import execution_engine, identity_engine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory profile store  (user_id -> title -> _ProfileState)
# ---------------------------------------------------------------------------

class _ProfileState:
    """Mutable internal state backing a PlayerTwinProfile."""

    def __init__(self, user_id: str, title: str) -> None:
        self.user_id = user_id
        self.title = title
        self.sessions_analyzed: int = 0
        self.panic_patterns: list[PanicPattern] = []
        self.tendency_entries: list[TendencyEntry] = []
        self.created_at: datetime = _now()
        self.updated_at: datetime = _now()


_profiles: dict[str, dict[str, _ProfileState]] = {}

# Population benchmark data (stub — real data comes from ForgeDataFabric)
_POPULATION_BENCHMARKS: dict[str, dict[str, list[float]]] = {}

# Minimum sessions for a "confident" profile
_CONFIDENT_THRESHOLD = 10


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_state(user_id: str, title: str) -> _ProfileState:
    _profiles.setdefault(user_id, {})
    if title not in _profiles[user_id]:
        _profiles[user_id][title] = _ProfileState(user_id, title)
    return _profiles[user_id][title]


# ---------------------------------------------------------------------------
# Core public API
# ---------------------------------------------------------------------------

def get_profile(user_id: str, title: str) -> PlayerTwinProfile:
    """Return the full digital model for a player in a specific title."""
    state = _ensure_state(user_id, title)
    identity = identity_engine.get_identity(user_id, title)
    exec_scores = execution_engine.get_all_scores(user_id, title)
    tendencies = TendencyMap(
        title=title,
        entries=state.tendency_entries,
        dominant_style=identity.style,
        last_updated=state.updated_at,
    )

    confidence = min(1.0, state.sessions_analyzed / _CONFIDENT_THRESHOLD)

    return PlayerTwinProfile(
        user_id=user_id,
        title=title,
        identity=identity,
        execution_scores=exec_scores,
        panic_patterns=state.panic_patterns,
        tendencies=tendencies,
        sessions_analyzed=state.sessions_analyzed,
        confidence=round(confidence, 4),
        created_at=state.created_at,
        updated_at=state.updated_at,
    )


def update_from_session(user_id: str, session: SessionData) -> PlayerTwinProfile:
    """Learn from a new completed game session (called by LoopAI).

    1. Feed execution data into ExecutionEngine.
    2. Derive identity signals via IdentityEngine.
    3. Extract panic patterns and tendencies.
    4. Return the updated profile.
    """
    title = session.title
    state = _ensure_state(user_id, title)

    # 1. Execution observations
    execution_engine.ingest_session(user_id, session)

    # 2. Identity adjustment
    identity_engine.derive_identity_from_session(user_id, session)

    # 3. Panic patterns
    _extract_panic_patterns(state, session)

    # 4. Tendencies
    _extract_tendencies(state, session)

    state.sessions_analyzed += 1
    state.updated_at = _now()

    logger.info(
        "PlayerTwin updated user=%s title=%s sessions=%d",
        user_id, title, state.sessions_analyzed,
    )
    return get_profile(user_id, title)


def get_execution_ceiling(user_id: str, title: str, skill: str) -> ExecutionScore:
    """What can the player reliably execute for a given skill?"""
    return execution_engine.score_execution(user_id, title, skill)


def get_panic_patterns(user_id: str, title: str) -> list[PanicPattern]:
    """How does the player perform under pressure?"""
    state = _ensure_state(user_id, title)
    return list(state.panic_patterns)


def get_tendencies(user_id: str, title: str) -> TendencyMap:
    """Play style tendencies for a specific title."""
    state = _ensure_state(user_id, title)
    identity = identity_engine.get_identity(user_id, title)
    return TendencyMap(
        title=title,
        entries=state.tendency_entries,
        dominant_style=identity.style,
        last_updated=state.updated_at,
    )


def can_execute(user_id: str, recommendation: RecommendationInput) -> CanExecuteResponse:
    """Can this player actually perform the recommended action?

    Combines execution ceiling check (can they mechanically do it?) with
    identity fit (does it match how they play?).
    """
    # Check each required skill
    limiting: list[str] = []
    min_score = 1.0
    title = "unknown"

    # We need a title — derive from existing profiles
    user_titles = list(_profiles.get(user_id, {}).keys())
    if user_titles:
        title = user_titles[0]

    for skill in recommendation.required_skills:
        es = execution_engine.score_execution(user_id, title, skill)
        if es.score < recommendation.difficulty:
            limiting.append(skill)
        min_score = min(min_score, es.score)

    # Identity filter
    identity = identity_engine.get_identity(user_id, title)
    identity_check = identity_engine.filter_recommendation(recommendation, identity)

    can_do = len(limiting) == 0 and identity_check.can_execute
    all_limiting = limiting + identity_check.limiting_skills

    confidence = min_score * identity_check.confidence if recommendation.required_skills else identity_check.confidence

    suggestion = None
    if not can_do:
        if limiting:
            suggestion = f"Player needs to improve: {', '.join(limiting)}. "
        if identity_check.suggestion:
            suggestion = (suggestion or "") + identity_check.suggestion

    return CanExecuteResponse(
        can_execute=can_do,
        confidence=round(confidence, 4),
        limiting_skills=all_limiting,
        suggestion=suggestion,
    )


def compare_to_benchmark(
    user_id: str,
    title: str,
    percentile: int = 50,
) -> BenchmarkComparison:
    """Compare a player to a population percentile.

    Uses population benchmark data when available. Falls back to a
    simple mapping from raw execution scores to estimated percentiles.
    """
    exec_scores = execution_engine.get_all_scores(user_id, title)
    dimensions: dict[str, float] = {}
    for es in exec_scores:
        # Simple heuristic: raw score * 100 ≈ percentile (placeholder)
        dimensions[es.skill] = round(es.score * 100, 1)

    values = list(dimensions.values())
    overall = round(sum(values) / len(values), 1) if values else 0.0

    strengths = [k for k, v in dimensions.items() if v >= 70]
    weaknesses = [k for k, v in dimensions.items() if v < 40]

    return BenchmarkComparison(
        title=title,
        target_percentile=percentile,
        dimensions=dimensions,
        overall_percentile=overall,
        strengths=strengths,
        weaknesses=weaknesses,
    )


def bootstrap_from_sessions(user_id: str, sessions: list[SessionData]) -> PlayerTwinProfile:
    """Build an initial profile from the first few sessions (onboarding).

    Processes each session in order, then returns the resulting profile.
    Minimum 1 session required; 3+ recommended for reasonable confidence.
    """
    if not sessions:
        raise ValueError("At least one session is required for bootstrapping")

    title = sessions[0].title
    for session in sessions:
        update_from_session(user_id, session)

    profile = get_profile(user_id, title)
    logger.info(
        "PlayerTwin bootstrapped user=%s title=%s from %d sessions (confidence=%.2f)",
        user_id, title, len(sessions), profile.confidence,
    )
    return profile


# ---------------------------------------------------------------------------
# Internal extraction helpers
# ---------------------------------------------------------------------------

def _extract_panic_patterns(state: _ProfileState, session: SessionData) -> None:
    """Detect panic patterns from pressure moments in a session."""
    for pm in session.pressure_moments:
        outcome = pm.get("outcome", 1.0)
        if outcome < 0.4:  # poor performance under pressure
            pattern_id = pm.get("pattern", "unknown_panic")
            trigger = pm.get("trigger", "pressure_situation")
            description = pm.get("description", f"Poor execution during {trigger}")

            # Update existing or create new
            existing = next((p for p in state.panic_patterns if p.pattern_id == pattern_id), None)
            if existing:
                # Increase frequency
                existing.frequency = min(1.0, round(existing.frequency + 0.1, 4))
                existing.last_observed = _now()
            else:
                state.panic_patterns.append(
                    PanicPattern(
                        pattern_id=pattern_id,
                        title=state.title,
                        description=description,
                        trigger=trigger,
                        frequency=0.3,
                        severity=round(1.0 - outcome, 4),
                        last_observed=_now(),
                    )
                )


def _extract_tendencies(state: _ProfileState, session: SessionData) -> None:
    """Derive tendency signals from play-by-play data."""
    play_categories: dict[str, int] = {}
    total_plays = len(session.plays)
    if total_plays == 0:
        return

    for play in session.plays:
        category = play.get("category", "general")
        play_categories[category] = play_categories.get(category, 0) + 1

    for category, count in play_categories.items():
        weight = round(count / total_plays, 4)
        # Update or add
        existing = next(
            (e for e in state.tendency_entries if e.category == category),
            None,
        )
        if existing:
            # EMA blend
            existing.weight = round(existing.weight * 0.7 + weight * 0.3, 4)
        else:
            state.tendency_entries.append(
                TendencyEntry(
                    category=category,
                    tendency=f"uses_{category}",
                    weight=weight,
                    context=session.mode.value,
                )
            )


# ---------------------------------------------------------------------------
# Testing helpers
# ---------------------------------------------------------------------------

def reset_store() -> None:
    """Clear all in-memory profile data. For testing only."""
    _profiles.clear()
    execution_engine.reset_store()
    identity_engine.reset_store()

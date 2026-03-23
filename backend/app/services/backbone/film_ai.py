"""FilmAI — replay analysis and pattern detection engine.

Phase 1: Manual tag-based analysis (human tags key moments).
Phase 3: VisionAudioForge integration for automated computer-vision analysis.

Provides replay breakdowns, mistake classification, cross-replay pattern
detection, and manual moment tagging.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from app.schemas.film import (
    FilmBreakdown,
    MistakeCategory,
    MistakeClassification,
    PatternDetection,
    ReplayAnalysis,
    TaggedMoment,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory stores (replaced by DB in production)
# ---------------------------------------------------------------------------

_replay_analyses: dict[str, ReplayAnalysis] = {}       # replay_id -> analysis
_tagged_moments: dict[str, list[TaggedMoment]] = defaultdict(list)  # replay_id -> moments
_user_replays: dict[str, dict[str, list[str]]] = defaultdict(
    lambda: defaultdict(list)
)  # user_id -> title -> [replay_ids]


def reset_store() -> None:
    """Clear all in-memory state (for testing)."""
    _replay_analyses.clear()
    _tagged_moments.clear()
    _user_replays.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_id() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_replay(user_id: str, replay_data: dict[str, Any]) -> ReplayAnalysis:
    """Produce a replay breakdown from manually-tagged data.

    Phase 1 relies on ``replay_data`` containing pre-tagged moments.
    Phase 3 will feed raw video through VisionAudioForge instead.
    """
    replay_id = replay_data.get("replay_id", _generate_id())
    title = replay_data.get("title", "unknown")

    # Extract pre-tagged moments from input
    raw_moments = replay_data.get("tagged_moments", [])
    moments = [
        TaggedMoment(
            replay_id=replay_id,
            timestamp=m.get("timestamp", 0.0),
            tag=m.get("tag", "untagged"),
            notes=m.get("notes", ""),
        )
        for m in raw_moments
    ]

    # Classify mistakes from moments tagged as errors
    mistakes = _extract_mistakes(moments)

    analysis = ReplayAnalysis(
        replay_id=replay_id,
        user_id=user_id,
        title=title,
        tagged_moments=moments,
        mistakes=mistakes,
        summary=_build_summary(moments, mistakes),
        analyzed_at=_now(),
    )

    # Persist
    _replay_analyses[replay_id] = analysis
    _tagged_moments[replay_id] = moments
    _user_replays[user_id][title].append(replay_id)

    logger.info("Analyzed replay %s for user %s (%s)", replay_id, user_id, title)
    return analysis


def classify_mistakes(
    replay_analysis: ReplayAnalysis,
) -> list[MistakeClassification]:
    """Categorize mistakes found in a replay analysis.

    Classification heuristic (Phase 1 — rule-based):
    - Tags containing 'read' / 'coverage' → READ_ERROR
    - Tags containing 'drop' / 'miss' / 'timing' → EXECUTION_ERROR
    - Tags containing 'scheme' / 'play_call' / 'formation' → SCHEME_ERROR
    """
    return _extract_mistakes(replay_analysis.tagged_moments)


def detect_patterns(
    user_id: str, title: str, sessions: int = 10
) -> list[PatternDetection]:
    """Scan last *sessions* replays for recurring patterns."""
    replay_ids = _user_replays.get(user_id, {}).get(title, [])
    recent_ids = replay_ids[-sessions:]

    if not recent_ids:
        return []

    # Aggregate tag frequencies across replays
    tag_counts: dict[str, int] = defaultdict(int)
    evidence: dict[str, list[str]] = defaultdict(list)

    for rid in recent_ids:
        seen_tags: set[str] = set()
        for moment in _tagged_moments.get(rid, []):
            if moment.tag not in seen_tags:
                tag_counts[moment.tag] += 1
                evidence[moment.tag].append(rid)
                seen_tags.add(moment.tag)

    total = len(recent_ids)
    patterns: list[PatternDetection] = []
    for tag, count in tag_counts.items():
        freq = count / total
        if freq >= 0.3:  # appears in ≥ 30 % of sessions
            patterns.append(
                PatternDetection(
                    user_id=user_id,
                    title=title,
                    pattern_name=tag,
                    description=f"'{tag}' detected in {count}/{total} recent sessions",
                    frequency=round(freq, 3),
                    sessions_scanned=total,
                    evidence_replay_ids=evidence[tag],
                    detected_at=_now(),
                )
            )

    logger.info(
        "Detected %d patterns for user %s in %s (last %d sessions)",
        len(patterns), user_id, title, total,
    )
    return patterns


def generate_breakdown(replay_id: str) -> FilmBreakdown:
    """Build a full film breakdown for a previously-analyzed replay."""
    analysis = _replay_analyses.get(replay_id)
    if analysis is None:
        raise ValueError(f"No analysis found for replay {replay_id}")

    mistake_summary: dict[MistakeCategory, int] = defaultdict(int)
    for m in analysis.mistakes:
        mistake_summary[m.category] += 1

    key_moments = [
        m for m in analysis.tagged_moments if m.tag in {"turnover", "big_play", "clutch"}
    ]

    recommendations = _build_recommendations(analysis.mistakes)

    return FilmBreakdown(
        replay_id=replay_id,
        analysis=analysis,
        key_moments=key_moments,
        mistake_summary=dict(mistake_summary),
        recommendations=recommendations,
    )


def tag_moment(
    replay_id: str, timestamp: float, tag: str, notes: str = ""
) -> TaggedMoment:
    """Manually tag a moment in a replay (Phase 1 human-in-the-loop)."""
    moment = TaggedMoment(
        replay_id=replay_id,
        timestamp=timestamp,
        tag=tag,
        notes=notes,
        created_at=_now(),
    )
    _tagged_moments[replay_id].append(moment)

    # Update the stored analysis if it exists
    if replay_id in _replay_analyses:
        _replay_analyses[replay_id].tagged_moments.append(moment)

    logger.info("Tagged moment at %.1fs in replay %s: %s", timestamp, replay_id, tag)
    return moment


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_READ_KEYWORDS = {"read", "coverage", "misread", "anticipation"}
_EXEC_KEYWORDS = {"drop", "miss", "timing", "whiff", "fumble", "overthrow"}
_SCHEME_KEYWORDS = {"scheme", "play_call", "formation", "audible", "wrong_play"}


def _classify_tag(tag: str) -> MistakeCategory | None:
    """Map a tag string to a mistake category (or None if not a mistake)."""
    tag_lower = tag.lower()
    for kw in _READ_KEYWORDS:
        if kw in tag_lower:
            return MistakeCategory.READ_ERROR
    for kw in _EXEC_KEYWORDS:
        if kw in tag_lower:
            return MistakeCategory.EXECUTION_ERROR
    for kw in _SCHEME_KEYWORDS:
        if kw in tag_lower:
            return MistakeCategory.SCHEME_ERROR
    return None


def _extract_mistakes(moments: list[TaggedMoment]) -> list[MistakeClassification]:
    mistakes: list[MistakeClassification] = []
    for m in moments:
        category = _classify_tag(m.tag)
        if category is not None:
            mistakes.append(
                MistakeClassification(
                    moment_timestamp=m.timestamp,
                    category=category,
                    description=m.notes or f"Detected from tag '{m.tag}'",
                    severity=0.5,
                    context={"tag": m.tag},
                )
            )
    return mistakes


def _build_summary(
    moments: list[TaggedMoment], mistakes: list[MistakeClassification]
) -> str:
    if not moments:
        return "No moments tagged."
    parts = [f"{len(moments)} moment(s) tagged"]
    if mistakes:
        parts.append(f"{len(mistakes)} mistake(s) classified")
    return "; ".join(parts) + "."


def _build_recommendations(mistakes: list[MistakeClassification]) -> list[str]:
    recs: list[str] = []
    categories = {m.category for m in mistakes}
    if MistakeCategory.READ_ERROR in categories:
        recs.append("Focus on pre-snap reads and coverage recognition drills.")
    if MistakeCategory.EXECUTION_ERROR in categories:
        recs.append("Spend time in practice mode refining mechanical execution.")
    if MistakeCategory.SCHEME_ERROR in categories:
        recs.append("Review situational play-calling and formation selection.")
    return recs

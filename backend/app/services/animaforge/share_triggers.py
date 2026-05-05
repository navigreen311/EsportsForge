"""Share-Win trigger detection (Agent #9).

After every session-end / drill-complete, ``check_share_win_triggers`` is called
to determine whether the player has hit a milestone worth a branded share card.

Trigger types (per blueprint Section 5):
    - ``tournament-win``        — won the tournament final this session
    - ``benchmark-milestone``   — newly reached top-10% in any BenchmarkAI metric
    - ``win-streak``            — streak reaches one of {5, 10, 15, 20}
    - ``impactrank-fix``        — a confirmed ROI improvement of >= 3% win-rate
    - ``playertwin-milestone``  — PlayerTwin first crosses 75% accuracy

Each detector is its own pure function so it can be unit-tested independently
on synthetic ``session_data`` without spinning up the database. The orchestrator
``check_share_win_triggers`` composes them, swallowing failures so that trigger
plumbing never blocks the session-end response.

When the data fetches the blueprint references (``getBenchmarkRankings``,
``getCurrentStreak``, ``getRecentROIConfirmations``) are not yet wired into
EsportsForge, the detector emits a ``# TODO`` and returns ``[]``. That keeps
this slice mergeable now; data wiring is a follow-up.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

VALID_TRIGGER_TYPES: tuple[str, ...] = (
    "tournament-win",
    "benchmark-milestone",
    "win-streak",
    "impactrank-fix",
    "playertwin-milestone",
)

WIN_STREAK_MILESTONES: tuple[int, ...] = (5, 10, 15, 20)
PLAYER_TWIN_THRESHOLD: float = 0.75
IMPACTRANK_MIN_IMPROVEMENT_PCT: float = 3.0
BENCHMARK_TOP_PERCENTILE: int = 10


@dataclass
class ShareTrigger:
    """A single share-win trigger ready for spec-building + render."""

    type: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "data": dict(self.data)}


# ---------------------------------------------------------------------------
# Per-trigger detectors (pure functions — independently testable)
# ---------------------------------------------------------------------------

def detect_tournament_win(
    title_id: str,
    session_data: dict[str, Any],
) -> ShareTrigger | None:
    """Tournament final win → tournament-win trigger.

    The session-end payload must include::

        {"mode": "tournament", "result": "win",
         "tournament_final": True,
         "tournament_name": "...",
         "tournament_record": "..."}
    """
    if session_data.get("mode") != "tournament":
        return None
    if session_data.get("result") != "win":
        return None
    if not session_data.get("tournament_final"):
        return None

    return ShareTrigger(
        type="tournament-win",
        data={
            "tournament_name": session_data.get("tournament_name", "Tournament"),
            "record": session_data.get("tournament_record", ""),
            "title_id": title_id,
        },
    )


async def detect_benchmark_milestone(
    user_id: str,
    title_id: str,
    session_data: dict[str, Any],
) -> list[ShareTrigger]:
    """Newly-reached top-10% percentile in any BenchmarkAI metric.

    Reads from session_data['new_benchmarks'] when the session orchestrator
    pre-computes them; otherwise falls back to a pluggable rankings fetch.
    Until BenchmarkAI exposes ``get_benchmark_rankings`` we read whatever the
    session payload provides — which is fine for unit tests and for the
    session-end pipeline once Agent #N wires it in.
    """
    triggers: list[ShareTrigger] = []

    # Primary path: session-end payload pre-fills new percentile achievements.
    new_benchmarks = session_data.get("new_benchmarks") or []
    for metric in new_benchmarks:
        try:
            percentile = int(metric.get("percentile", 100))
            previously = bool(metric.get("previously_achieved", False))
            name = metric.get("name") or metric.get("skill") or "Skill"
        except (TypeError, ValueError):
            continue
        if percentile <= BENCHMARK_TOP_PERCENTILE and not previously:
            triggers.append(
                ShareTrigger(
                    type="benchmark-milestone",
                    data={
                        "skill": name,
                        "percentile": percentile,
                        "title_id": title_id,
                    },
                )
            )

    # TODO(animaforge): wire to BenchmarkAI ranking service once exposed —
    # blueprint references getBenchmarkRankings(userId, titleId).
    return triggers


async def detect_win_streak(
    user_id: str,
    title_id: str,
    session_data: dict[str, Any],
) -> ShareTrigger | None:
    """Streak hits 5 / 10 / 15 / 20 → win-streak trigger."""
    streak = session_data.get("current_streak")
    if streak is None:
        # TODO(animaforge): wire to streak service — blueprint references
        # getCurrentStreak(userId, titleId). Until then we rely on the
        # session-end payload to include `current_streak`.
        return None
    try:
        streak_int = int(streak)
    except (TypeError, ValueError):
        return None
    if streak_int not in WIN_STREAK_MILESTONES:
        return None
    return ShareTrigger(
        type="win-streak",
        data={"streak": streak_int, "title_id": title_id},
    )


async def detect_impactrank_fix(
    user_id: str,
    title_id: str,
    session_data: dict[str, Any],
) -> list[ShareTrigger]:
    """ImpactRank fix confirmed with >= 3% win-rate improvement.

    Reads ``roi_confirmations`` from session_data. Each entry should have
    ``priority_name`` and ``win_rate_improvement`` (float, percent).
    """
    triggers: list[ShareTrigger] = []
    confirmations = session_data.get("roi_confirmations") or []
    for roi in confirmations:
        try:
            improvement = float(roi.get("win_rate_improvement", 0))
            fix_name = roi.get("priority_name") or roi.get("fix_name") or "Fix"
        except (TypeError, ValueError):
            continue
        if improvement >= IMPACTRANK_MIN_IMPROVEMENT_PCT:
            triggers.append(
                ShareTrigger(
                    type="impactrank-fix",
                    data={
                        "fix_name": fix_name,
                        "improvement": round(improvement, 1),
                        "title_id": title_id,
                    },
                )
            )
    # TODO(animaforge): wire to ImpactRank service — blueprint references
    # getRecentROIConfirmations(userId).
    return triggers


def detect_playertwin_milestone(
    title_id: str,
    session_data: dict[str, Any],
) -> ShareTrigger | None:
    """PlayerTwin crosses 75% prediction accuracy for the first time."""
    twin = session_data.get("player_twin") or {}
    accuracy = twin.get("accuracy")
    previously = bool(twin.get("threshold_75_previously_reached", False))
    if accuracy is None or previously:
        return None
    try:
        accuracy_f = float(accuracy)
    except (TypeError, ValueError):
        return None
    if accuracy_f < PLAYER_TWIN_THRESHOLD:
        return None
    return ShareTrigger(
        type="playertwin-milestone",
        data={
            "accuracy": round(accuracy_f, 3),
            "games_played": int(twin.get("games_played", 0) or 0),
            "insight": twin.get("insight"),
            "title_id": title_id,
        },
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def check_share_win_triggers(
    user_id: str,
    title_id: str,
    session_data: dict[str, Any],
) -> list[ShareTrigger]:
    """Run every detector and return the union of fired triggers.

    Errors in any single detector are logged and swallowed so trigger
    detection never blocks session-end response delivery.
    """
    triggers: list[ShareTrigger] = []

    try:
        if (t := detect_tournament_win(title_id, session_data)) is not None:
            triggers.append(t)
    except Exception:  # noqa: BLE001
        logger.exception("detect_tournament_win failed")

    try:
        triggers.extend(await detect_benchmark_milestone(user_id, title_id, session_data))
    except Exception:  # noqa: BLE001
        logger.exception("detect_benchmark_milestone failed")

    try:
        if (t := await detect_win_streak(user_id, title_id, session_data)) is not None:
            triggers.append(t)
    except Exception:  # noqa: BLE001
        logger.exception("detect_win_streak failed")

    try:
        triggers.extend(await detect_impactrank_fix(user_id, title_id, session_data))
    except Exception:  # noqa: BLE001
        logger.exception("detect_impactrank_fix failed")

    try:
        if (t := detect_playertwin_milestone(title_id, session_data)) is not None:
            triggers.append(t)
    except Exception:  # noqa: BLE001
        logger.exception("detect_playertwin_milestone failed")

    return triggers


__all__ = [
    "BENCHMARK_TOP_PERCENTILE",
    "IMPACTRANK_MIN_IMPROVEMENT_PCT",
    "PLAYER_TWIN_THRESHOLD",
    "ShareTrigger",
    "VALID_TRIGGER_TYPES",
    "WIN_STREAK_MILESTONES",
    "check_share_win_triggers",
    "detect_benchmark_milestone",
    "detect_impactrank_fix",
    "detect_playertwin_milestone",
    "detect_tournament_win",
    "detect_win_streak",
]

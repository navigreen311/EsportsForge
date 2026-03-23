"""Forge Data Fabric — the central data nervous system for EsportsForge.

Every piece of game data flows through the Data Fabric: sessions, replays,
opponent records, and patch context.  The fabric validates, transforms,
quality-scores, and persists data — ensuring downstream agents always
receive clean, trustworthy information.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.backbone.data_adapters import (
    BaseDataAdapter,
    NormalisedSession,
    ValidationResult,
    get_adapter,
)
from app.services.backbone.entity_resolution import (
    BehavioralFingerprint,
    OpponentRecord,
    get_behavioral_fingerprint,
    resolve_opponent,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DATA_FRESHNESS_HOURS = 72         # data older than this is flagged stale
_MIN_CONFIDENCE_THRESHOLD = 0.3    # below this, data is rejected outright
_HIGH_CONFIDENCE_THRESHOLD = 0.8   # above this, data is considered reliable
_COMPLETENESS_WEIGHT = 0.35
_FRESHNESS_WEIGHT = 0.30
_CONSISTENCY_WEIGHT = 0.20
_SAMPLE_SIZE_WEIGHT = 0.15

# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------

@dataclass
class DataQualityScore:
    """Multi-dimensional quality assessment of a data record."""

    completeness: float = 0.0    # 0-1, fraction of expected fields present
    freshness: float = 0.0       # 0-1, 1 = just recorded, 0 = stale
    consistency: float = 0.0     # 0-1, internal consistency checks
    sample_size_score: float = 0.0  # 0-1, normalised by title expectations
    overall: float = 0.0        # weighted composite

    @property
    def is_acceptable(self) -> bool:
        return self.overall >= _MIN_CONFIDENCE_THRESHOLD

    @property
    def is_reliable(self) -> bool:
        return self.overall >= _HIGH_CONFIDENCE_THRESHOLD


@dataclass
class IngestResult:
    """Outcome of an ingest operation."""

    success: bool
    session_id: str = ""
    quality: DataQualityScore = field(default_factory=DataQualityScore)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


@dataclass
class PatchContext:
    """Current patch / meta state for a title."""

    title: str
    patch_version: str
    release_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    meta_state: str = "stable"      # "stable", "shifting", "new_patch"
    hotfix_applied: bool = False
    notes: str = ""


@dataclass
class DataQualityReport:
    """Aggregate quality stats for a user's data."""

    user_id: str
    total_sessions: int = 0
    avg_quality: float = 0.0
    reliable_pct: float = 0.0        # % of sessions above reliable threshold
    stale_pct: float = 0.0           # % of sessions with stale data
    titles: dict[str, int] = field(default_factory=dict)
    quality_trend: str = "stable"    # "improving", "stable", "degrading"
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# In-memory stores (will be backed by PostgreSQL / Redis)
# ---------------------------------------------------------------------------

# user_id -> title -> list[NormalisedSession]
_session_store: dict[str, dict[str, list[NormalisedSession]]] = {}

# session_id -> DataQualityScore
_quality_store: dict[str, DataQualityScore] = {}

# title -> PatchContext
_patch_store: dict[str, PatchContext] = {
    "madden": PatchContext(title="madden", patch_version="25.3.1", meta_state="stable"),
    "cfb": PatchContext(title="cfb", patch_version="2.1.0", meta_state="shifting"),
}

# opponent_id -> title -> list[NormalisedSession]
_opponent_session_store: dict[str, dict[str, list[NormalisedSession]]] = {}

# replay_id -> raw replay data
_replay_store: dict[str, dict[str, Any]] = {}


def _reset_stores() -> None:
    """Clear all stores (test helper)."""
    _session_store.clear()
    _quality_store.clear()
    _opponent_session_store.clear()
    _replay_store.clear()


# ---------------------------------------------------------------------------
# Data quality engine
# ---------------------------------------------------------------------------

def validate_data_quality(data: dict[str, Any]) -> DataQualityScore:
    """Score data quality across completeness, freshness, consistency, sample size.

    Returns a DataQualityScore with an overall confidence from 0.0 to 1.0.
    """
    score = DataQualityScore()

    # --- Completeness: fraction of expected fields present ---
    expected_keys = {"session_id", "user_id", "plays", "result", "score_home",
                     "score_away", "mode", "title", "opponent_id", "duration_seconds"}
    present = sum(1 for k in expected_keys if data.get(k) not in (None, "", [], {}))
    score.completeness = present / len(expected_keys)

    # --- Freshness: how recently was this data recorded ---
    timestamp_str = data.get("timestamp") or data.get("recorded_at")
    if timestamp_str:
        try:
            if isinstance(timestamp_str, datetime):
                recorded = timestamp_str
            else:
                recorded = datetime.fromisoformat(str(timestamp_str))
            if recorded.tzinfo is None:
                recorded = recorded.replace(tzinfo=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - recorded).total_seconds() / 3600
            score.freshness = max(0.0, 1.0 - (age_hours / _DATA_FRESHNESS_HOURS))
        except (ValueError, TypeError):
            score.freshness = 0.5  # can't determine, give neutral score
    else:
        score.freshness = 1.0  # assume fresh if no timestamp (just recorded)

    # --- Consistency: internal logic checks ---
    consistency_checks_passed = 0
    consistency_checks_total = 0

    plays = data.get("plays", [])
    score_home = data.get("score_home", 0)
    score_away = data.get("score_away", 0)

    # Check: result matches score comparison
    result = data.get("result", "")
    if result and score_home is not None and score_away is not None:
        consistency_checks_total += 1
        if (result == "win" and score_home > score_away) or \
           (result == "loss" and score_home < score_away) or \
           (result == "draw" and score_home == score_away):
            consistency_checks_passed += 1

    # Check: plays have sequential structure
    if plays:
        consistency_checks_total += 1
        has_structure = all(isinstance(p, dict) for p in plays)
        if has_structure:
            consistency_checks_passed += 1

    # Check: quarter values are in valid range
    if plays:
        consistency_checks_total += 1
        quarters = [p.get("quarter", 0) for p in plays if isinstance(p, dict)]
        if quarters and all(0 <= q <= 6 for q in quarters):  # 5-6 for OT
            consistency_checks_passed += 1

    # Check: yards are reasonable
    if plays:
        consistency_checks_total += 1
        yards_vals = [p.get("yards", 0) for p in plays if isinstance(p, dict)]
        if yards_vals and all(-50 <= y <= 110 for y in yards_vals):
            consistency_checks_passed += 1

    score.consistency = (
        consistency_checks_passed / consistency_checks_total
        if consistency_checks_total > 0
        else 0.5
    )

    # --- Sample size score ---
    play_count = len(plays)
    # A full game is typically 60-120 plays; normalise against 80
    score.sample_size_score = min(1.0, play_count / 80.0)

    # --- Weighted composite ---
    score.overall = round(
        score.completeness * _COMPLETENESS_WEIGHT
        + score.freshness * _FRESHNESS_WEIGHT
        + score.consistency * _CONSISTENCY_WEIGHT
        + score.sample_size_score * _SAMPLE_SIZE_WEIGHT,
        4,
    )

    logger.debug(
        "data quality scored",
        extra={
            "completeness": score.completeness,
            "freshness": score.freshness,
            "consistency": score.consistency,
            "sample_size": score.sample_size_score,
            "overall": score.overall,
        },
    )
    return score


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

def ingest_session(session_data: dict[str, Any]) -> IngestResult:
    """Validate, transform, and persist a game session.

    Pipeline:
    1. Select title adapter.
    2. Adapter-level validation.
    3. Quality scoring.
    4. Reject if below minimum confidence.
    5. Ingest and transform via adapter.
    6. Persist to stores.
    7. Update opponent records.
    """
    t0 = time.monotonic()
    title = session_data.get("title", "generic")
    adapter: BaseDataAdapter = get_adapter(title)

    # Step 1 — adapter validation
    val: ValidationResult = adapter.validate(session_data)
    if not val.is_valid:
        elapsed = (time.monotonic() - t0) * 1000
        logger.warning("session rejected by adapter validation", extra={"errors": val.errors})
        return IngestResult(
            success=False,
            errors=val.errors,
            warnings=val.warnings,
            elapsed_ms=round(elapsed, 2),
        )

    # Step 2 — quality scoring
    quality = validate_data_quality(session_data)
    if not quality.is_acceptable:
        elapsed = (time.monotonic() - t0) * 1000
        logger.warning(
            "session rejected: quality below threshold",
            extra={"overall": quality.overall, "threshold": _MIN_CONFIDENCE_THRESHOLD},
        )
        return IngestResult(
            success=False,
            quality=quality,
            errors=[f"Quality score {quality.overall:.2f} below minimum {_MIN_CONFIDENCE_THRESHOLD}"],
            warnings=val.warnings,
            elapsed_ms=round(elapsed, 2),
        )

    # Step 3 — ingest and transform
    session: NormalisedSession = adapter.ingest(session_data)
    session = adapter.transform(session)

    # Step 4 — persist session
    user_id = session.user_id
    _session_store.setdefault(user_id, {}).setdefault(title, []).append(session)
    _quality_store[session.session_id] = quality

    # Step 5 — update opponent store if opponent present
    if session.opponent_id:
        opponent = resolve_opponent(session.opponent_id, title)
        opponent.encounter_count += 1
        _opponent_session_store.setdefault(opponent.opponent_id, {}).setdefault(
            title, []
        ).append(session)

    elapsed = (time.monotonic() - t0) * 1000
    logger.info(
        "session ingested",
        extra={
            "session_id": session.session_id,
            "title": title,
            "quality": quality.overall,
            "elapsed_ms": round(elapsed, 2),
        },
    )

    return IngestResult(
        success=True,
        session_id=session.session_id,
        quality=quality,
        warnings=val.warnings,
        elapsed_ms=round(elapsed, 2),
    )


def ingest_replay(replay_data: dict[str, Any]) -> IngestResult:
    """Process replay data with validation and storage.

    Replays are richer than live sessions — they contain full play-by-play
    with camera angles, audible info, and pre-snap reads.  We extract the
    session-equivalent data and also store the raw replay for film analysis.
    """
    t0 = time.monotonic()
    replay_id = replay_data.get("replay_id", "")
    if not replay_id:
        return IngestResult(success=False, errors=["Missing replay_id"])

    title = replay_data.get("title", "generic")
    adapter = get_adapter(title)

    # Validate the embedded session data
    session_payload = replay_data.get("session_data", replay_data)
    val = adapter.validate(session_payload)
    if not val.is_valid:
        elapsed = (time.monotonic() - t0) * 1000
        return IngestResult(success=False, errors=val.errors, elapsed_ms=round(elapsed, 2))

    quality = validate_data_quality(session_payload)
    if not quality.is_acceptable:
        elapsed = (time.monotonic() - t0) * 1000
        return IngestResult(
            success=False,
            quality=quality,
            errors=[f"Replay quality {quality.overall:.2f} below minimum"],
            elapsed_ms=round(elapsed, 2),
        )

    # Store raw replay for film analysis
    _replay_store[replay_id] = replay_data

    # Ingest session portion
    session = adapter.ingest(session_payload)
    session = adapter.transform(session)
    session.metadata["replay_id"] = replay_id
    session.metadata["has_audibles"] = bool(replay_data.get("audibles"))
    session.metadata["has_presnap_reads"] = bool(replay_data.get("presnap_reads"))

    user_id = session.user_id
    _session_store.setdefault(user_id, {}).setdefault(title, []).append(session)
    _quality_store[session.session_id] = quality

    elapsed = (time.monotonic() - t0) * 1000
    logger.info(
        "replay ingested",
        extra={"replay_id": replay_id, "session_id": session.session_id, "quality": quality.overall},
    )
    return IngestResult(
        success=True,
        session_id=session.session_id,
        quality=quality,
        elapsed_ms=round(elapsed, 2),
    )


# ---------------------------------------------------------------------------
# Entity resolution facade
# ---------------------------------------------------------------------------

def resolve_entity(identifier: str, title: str) -> OpponentRecord:
    """Match an opponent across sessions/platforms.

    Combines gamertag matching with behavioural fingerprinting.  If the
    opponent has prior session data, a fingerprint is generated and attached.
    """
    record = resolve_opponent(identifier, title)

    # Enrich with fingerprint if we have session data
    opp_sessions = _opponent_session_store.get(record.opponent_id, {}).get(title, [])
    if opp_sessions:
        all_plays: list[dict] = []
        for s in opp_sessions:
            all_plays.extend(p.raw for p in s.plays)

        fp = get_behavioral_fingerprint({"plays": all_plays, "sessions": [s.metadata for s in opp_sessions]})
        record.fingerprint = fp
        logger.debug("fingerprint attached to entity", extra={"opponent_id": record.opponent_id})

    return record


# ---------------------------------------------------------------------------
# Data retrieval
# ---------------------------------------------------------------------------

def get_player_data(
    user_id: str,
    title: str,
    time_range: timedelta | None = None,
) -> list[NormalisedSession]:
    """Retrieve clean, quality-filtered player data.

    Parameters
    ----------
    user_id : str
        The player whose data we need.
    title : str
        Game title to filter by.
    time_range : timedelta, optional
        If given, only return sessions within this window from now.

    Returns only sessions that passed quality checks at ingest time.
    """
    sessions = _session_store.get(user_id, {}).get(title, [])
    if not sessions:
        return []

    # Time-range filter
    if time_range is not None:
        cutoff = datetime.now(timezone.utc) - time_range
        sessions = [s for s in sessions if s.timestamp >= cutoff]

    # Quality filter — only return sessions with acceptable quality
    filtered: list[NormalisedSession] = []
    for s in sessions:
        q = _quality_store.get(s.session_id)
        if q and q.is_acceptable:
            filtered.append(s)
        elif q is None:
            # No quality record means it was ingested without scoring (legacy)
            filtered.append(s)

    logger.debug(
        "player data retrieved",
        extra={"user_id": user_id, "title": title, "total": len(sessions), "filtered": len(filtered)},
    )
    return filtered


def get_opponent_data(opponent_id: str, title: str) -> list[NormalisedSession]:
    """Retrieve all session data involving an opponent for a given title."""
    sessions = _opponent_session_store.get(opponent_id, {}).get(title, [])
    logger.debug("opponent data retrieved", extra={"opponent_id": opponent_id, "count": len(sessions)})
    return sessions


# ---------------------------------------------------------------------------
# Patch context
# ---------------------------------------------------------------------------

def get_patch_context(title: str) -> PatchContext:
    """Return the current patch version and meta state for a title.

    If no context is tracked for the title, returns a default 'unknown' context.
    """
    normalised = title.strip().lower()
    if normalised in _patch_store:
        ctx = _patch_store[normalised]
        # Check if patch is new (released within last 7 days)
        age = datetime.now(timezone.utc) - ctx.release_date
        if age < timedelta(days=7):
            ctx.meta_state = "new_patch"
        return ctx

    return PatchContext(
        title=normalised,
        patch_version="unknown",
        meta_state="unknown",
        notes="No patch tracking configured for this title",
    )


# ---------------------------------------------------------------------------
# Quality reporting
# ---------------------------------------------------------------------------

def get_data_quality_report(user_id: str) -> DataQualityReport:
    """Generate an aggregate data-quality report for a user across all titles."""
    report = DataQualityReport(user_id=user_id)

    user_sessions = _session_store.get(user_id, {})
    if not user_sessions:
        return report

    all_qualities: list[float] = []
    reliable_count = 0
    stale_count = 0
    total = 0

    for title, sessions in user_sessions.items():
        report.titles[title] = len(sessions)
        total += len(sessions)

        for s in sessions:
            q = _quality_store.get(s.session_id)
            if q:
                all_qualities.append(q.overall)
                if q.is_reliable:
                    reliable_count += 1
                if q.freshness < 0.3:
                    stale_count += 1

    report.total_sessions = total
    if all_qualities:
        report.avg_quality = round(sum(all_qualities) / len(all_qualities), 4)
        report.reliable_pct = round(reliable_count / len(all_qualities) * 100, 1)
        report.stale_pct = round(stale_count / len(all_qualities) * 100, 1)

    # Quality trend — compare first half vs second half of sessions
    if len(all_qualities) >= 4:
        mid = len(all_qualities) // 2
        first_half_avg = sum(all_qualities[:mid]) / mid
        second_half_avg = sum(all_qualities[mid:]) / (len(all_qualities) - mid)
        diff = second_half_avg - first_half_avg
        if diff > 0.05:
            report.quality_trend = "improving"
        elif diff < -0.05:
            report.quality_trend = "degrading"
        else:
            report.quality_trend = "stable"

    logger.info(
        "quality report generated",
        extra={
            "user_id": user_id,
            "total_sessions": report.total_sessions,
            "avg_quality": report.avg_quality,
        },
    )
    return report

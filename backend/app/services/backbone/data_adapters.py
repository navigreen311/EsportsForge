"""Game-title data adapters — normalise raw session/replay data per title.

Each supported title gets its own adapter that knows how to parse, validate,
and transform the raw data into a common internal format.  A factory
function selects the right adapter at runtime.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared data structures
# ---------------------------------------------------------------------------

@dataclass
class NormalisedPlay:
    """One play in title-agnostic form."""

    play_index: int
    play_type: str           # "run", "pass", "special", "penalty", etc.
    formation: str = ""
    scheme: str = ""
    result: str = ""         # "gain", "loss", "turnover", "score", …
    yards: float = 0.0
    down: int = 0
    distance: float = 0.0
    quarter: int = 0
    clock_seconds: int = 0
    is_blitz: bool = False
    tags: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalisedSession:
    """Title-agnostic session representation."""

    session_id: str
    title: str
    user_id: str
    opponent_id: str = ""
    mode: str = ""
    plays: list[NormalisedPlay] = field(default_factory=list)
    score_home: int = 0
    score_away: int = 0
    result: str = ""            # "win", "loss", "draw"
    duration_seconds: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ValidationResult:
    """Outcome of adapter-level validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    completeness: float = 1.0   # 0-1


# ---------------------------------------------------------------------------
# Base adapter
# ---------------------------------------------------------------------------

class BaseDataAdapter(ABC):
    """Interface every title adapter must implement."""

    title: str  # e.g. "madden", "cfb"

    @abstractmethod
    def ingest(self, raw_data: dict[str, Any]) -> NormalisedSession:
        """Parse raw data into a NormalisedSession."""

    @abstractmethod
    def transform(self, session: NormalisedSession) -> NormalisedSession:
        """Apply title-specific enrichments (scheme tagging, momentum, etc.)."""

    @abstractmethod
    def validate(self, raw_data: dict[str, Any]) -> ValidationResult:
        """Check raw data before ingestion."""


# ---------------------------------------------------------------------------
# Madden adapter
# ---------------------------------------------------------------------------

_MADDEN_REQUIRED_KEYS = {"session_id", "user_id", "plays"}
_MADDEN_SCHEME_KEYWORDS: dict[str, list[str]] = {
    "spread": ["shotgun", "empty", "trips", "bunch"],
    "west_coast": ["singleback", "slot", "flat", "screen"],
    "power_run": ["i_form", "strong", "counter", "dive", "iso"],
    "air_raid": ["shotgun", "empty", "four_wide", "mesh", "verticals"],
    "rpo": ["pistol", "read_option", "rpo", "zone_read"],
}


class MaddenDataAdapter(BaseDataAdapter):
    """Parse Madden play-by-play, detect offensive/defensive schemes, extract clock state."""

    title = "madden"

    # -- Validation ---------------------------------------------------------

    def validate(self, raw_data: dict[str, Any]) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        missing = _MADDEN_REQUIRED_KEYS - set(raw_data.keys())
        if missing:
            errors.append(f"Missing required keys: {missing}")

        plays = raw_data.get("plays", [])
        if not plays:
            errors.append("No plays in session data")
        elif len(plays) < 10:
            warnings.append(f"Very short session ({len(plays)} plays)")

        completeness = 1.0 - (len(missing) / len(_MADDEN_REQUIRED_KEYS))
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            completeness=max(0.0, completeness),
        )

    # -- Ingestion ----------------------------------------------------------

    def ingest(self, raw_data: dict[str, Any]) -> NormalisedSession:
        plays: list[NormalisedPlay] = []
        for idx, rp in enumerate(raw_data.get("plays", [])):
            play = NormalisedPlay(
                play_index=idx,
                play_type=_classify_play_type(rp),
                formation=rp.get("formation", ""),
                result=rp.get("result", ""),
                yards=float(rp.get("yards", 0)),
                down=int(rp.get("down", 0)),
                distance=float(rp.get("distance", 0)),
                quarter=int(rp.get("quarter", 0)),
                clock_seconds=_parse_clock(rp.get("clock", "")),
                is_blitz=rp.get("is_blitz", False),
                tags=rp.get("tags", []),
                raw=rp,
            )
            plays.append(play)

        session = NormalisedSession(
            session_id=raw_data.get("session_id", ""),
            title=self.title,
            user_id=raw_data.get("user_id", ""),
            opponent_id=raw_data.get("opponent_id", ""),
            mode=raw_data.get("mode", "h2h"),
            plays=plays,
            score_home=int(raw_data.get("score_home", 0)),
            score_away=int(raw_data.get("score_away", 0)),
            result=raw_data.get("result", ""),
            duration_seconds=int(raw_data.get("duration_seconds", 0)),
            metadata=raw_data.get("metadata", {}),
        )
        logger.info("madden session ingested", extra={"plays": len(plays), "sid": session.session_id})
        return session

    # -- Transformation (scheme detection, clock state) ---------------------

    def transform(self, session: NormalisedSession) -> NormalisedSession:
        session = self._detect_schemes(session)
        session = self._enrich_clock_state(session)
        return session

    def _detect_schemes(self, session: NormalisedSession) -> NormalisedSession:
        """Tag each play with the most likely offensive scheme."""
        for play in session.plays:
            formation_lower = play.formation.lower()
            best_scheme = "unknown"
            best_score = 0
            for scheme, keywords in _MADDEN_SCHEME_KEYWORDS.items():
                hits = sum(1 for kw in keywords if kw in formation_lower or kw in " ".join(play.tags).lower())
                if hits > best_score:
                    best_score = hits
                    best_scheme = scheme
            if best_score > 0:
                play.scheme = best_scheme
                if "scheme" not in play.tags:
                    play.tags.append(f"scheme:{best_scheme}")
        return session

    def _enrich_clock_state(self, session: NormalisedSession) -> NormalisedSession:
        """Add clock-pressure tags: two_minute_warning, end_of_half, hurry_up."""
        for play in session.plays:
            if play.quarter in (2, 4) and play.clock_seconds <= 120:
                play.tags.append("two_minute_warning")
            if play.quarter == 2 and play.clock_seconds <= 30:
                play.tags.append("end_of_half")
            if play.quarter == 4 and play.clock_seconds <= 120:
                play.tags.append("clutch_time")
        return session


# ---------------------------------------------------------------------------
# CFB (College Football) adapter
# ---------------------------------------------------------------------------

_CFB_REQUIRED_KEYS = {"session_id", "user_id"}


class CFBDataAdapter(BaseDataAdapter):
    """Parse College Football data with momentum tracking and recruiting data."""

    title = "cfb"

    def validate(self, raw_data: dict[str, Any]) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        missing = _CFB_REQUIRED_KEYS - set(raw_data.keys())
        if missing:
            errors.append(f"Missing required keys: {missing}")

        if not raw_data.get("plays") and not raw_data.get("drives"):
            warnings.append("No play or drive data found")

        completeness = 1.0 - (len(missing) / max(len(_CFB_REQUIRED_KEYS), 1))
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            completeness=max(0.0, completeness),
        )

    def ingest(self, raw_data: dict[str, Any]) -> NormalisedSession:
        plays: list[NormalisedPlay] = []
        for idx, rp in enumerate(raw_data.get("plays", [])):
            plays.append(NormalisedPlay(
                play_index=idx,
                play_type=_classify_play_type(rp),
                formation=rp.get("formation", ""),
                result=rp.get("result", ""),
                yards=float(rp.get("yards", 0)),
                down=int(rp.get("down", 0)),
                distance=float(rp.get("distance", 0)),
                quarter=int(rp.get("quarter", 0)),
                clock_seconds=_parse_clock(rp.get("clock", "")),
                is_blitz=rp.get("is_blitz", False),
                tags=rp.get("tags", []),
                raw=rp,
            ))

        session = NormalisedSession(
            session_id=raw_data.get("session_id", ""),
            title=self.title,
            user_id=raw_data.get("user_id", ""),
            opponent_id=raw_data.get("opponent_id", ""),
            mode=raw_data.get("mode", "dynasty"),
            plays=plays,
            score_home=int(raw_data.get("score_home", 0)),
            score_away=int(raw_data.get("score_away", 0)),
            result=raw_data.get("result", ""),
            duration_seconds=int(raw_data.get("duration_seconds", 0)),
            metadata=raw_data.get("metadata", {}),
        )
        logger.info("cfb session ingested", extra={"plays": len(plays), "sid": session.session_id})
        return session

    def transform(self, session: NormalisedSession) -> NormalisedSession:
        session = self._track_momentum(session)
        session = self._parse_recruiting(session)
        return session

    def _track_momentum(self, session: NormalisedSession) -> NormalisedSession:
        """Compute a rolling momentum score based on consecutive positive plays."""
        momentum = 0.0
        for play in session.plays:
            if play.yards > 0:
                momentum = min(1.0, momentum + 0.1)
            elif play.result in ("turnover", "fumble", "interception"):
                momentum = max(-1.0, momentum - 0.4)
            else:
                momentum *= 0.9  # decay toward neutral

            rounded = round(momentum, 2)
            play.tags.append(f"momentum:{rounded}")
            if abs(momentum) > 0.6:
                play.tags.append("momentum_swing")

        session.metadata["final_momentum"] = round(momentum, 2)
        return session

    def _parse_recruiting(self, session: NormalisedSession) -> NormalisedSession:
        """Extract recruiting context if present in metadata."""
        recruiting = session.metadata.get("recruiting", {})
        if not recruiting:
            return session

        stars = recruiting.get("avg_stars", 0)
        if stars >= 4.0:
            session.metadata["recruiting_tier"] = "elite"
        elif stars >= 3.0:
            session.metadata["recruiting_tier"] = "competitive"
        else:
            session.metadata["recruiting_tier"] = "developing"

        pipeline = recruiting.get("pipeline_size", 0)
        session.metadata["recruiting_depth"] = (
            "deep" if pipeline >= 15 else "moderate" if pipeline >= 8 else "thin"
        )
        return session


# ---------------------------------------------------------------------------
# Generic fallback adapter
# ---------------------------------------------------------------------------

class GenericDataAdapter(BaseDataAdapter):
    """Minimal adapter for titles without a specialised parser."""

    title = "generic"

    def validate(self, raw_data: dict[str, Any]) -> ValidationResult:
        errors: list[str] = []
        if not raw_data.get("session_id"):
            errors.append("Missing session_id")
        if not raw_data.get("user_id"):
            errors.append("Missing user_id")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def ingest(self, raw_data: dict[str, Any]) -> NormalisedSession:
        plays: list[NormalisedPlay] = []
        for idx, rp in enumerate(raw_data.get("plays", [])):
            plays.append(NormalisedPlay(
                play_index=idx,
                play_type=rp.get("type", "unknown"),
                raw=rp,
            ))

        return NormalisedSession(
            session_id=raw_data.get("session_id", ""),
            title=raw_data.get("title", "unknown"),
            user_id=raw_data.get("user_id", ""),
            opponent_id=raw_data.get("opponent_id", ""),
            plays=plays,
            metadata=raw_data.get("metadata", {}),
        )

    def transform(self, session: NormalisedSession) -> NormalisedSession:
        # No title-specific enrichment for generic adapter
        return session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify_play_type(raw_play: dict[str, Any]) -> str:
    """Determine canonical play type from raw play data."""
    pt = raw_play.get("type", raw_play.get("play_type", "")).lower()
    if any(kw in pt for kw in ("pass", "throw", "scramble")):
        return "pass"
    if any(kw in pt for kw in ("run", "rush", "carry", "qb_run")):
        return "run"
    if any(kw in pt for kw in ("punt", "kick", "fg", "field_goal", "kickoff")):
        return "special"
    if "penalty" in pt:
        return "penalty"
    return pt or "unknown"


def _parse_clock(clock_str: str) -> int:
    """Convert 'MM:SS' or raw seconds string to total seconds."""
    if not clock_str:
        return 0
    if ":" in str(clock_str):
        parts = str(clock_str).split(":")
        try:
            return int(parts[0]) * 60 + int(parts[1])
        except (ValueError, IndexError):
            return 0
    try:
        return int(float(clock_str))
    except (ValueError, TypeError):
        return 0


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_ADAPTER_REGISTRY: dict[str, type[BaseDataAdapter]] = {
    "madden": MaddenDataAdapter,
    "cfb": CFBDataAdapter,
}


def get_adapter(title: str) -> BaseDataAdapter:
    """Return the appropriate adapter for *title*, falling back to generic."""
    normalised = title.strip().lower()
    adapter_cls = _ADAPTER_REGISTRY.get(normalised, GenericDataAdapter)
    adapter = adapter_cls()
    if adapter_cls is GenericDataAdapter and normalised not in _ADAPTER_REGISTRY:
        logger.warning("no specialised adapter for title, using generic", extra={"title": title})
    return adapter

"""Entity Resolution — cross-session, cross-platform opponent matching.

Resolves opponents across sessions and platforms by combining gamertag
matching, platform ID lookups, and behavioral fingerprinting.  When two
records likely refer to the same human, they can be merged into a single
canonical opponent profile.
"""

from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class BehavioralFingerprint:
    """Quantified play-pattern signature for an opponent."""

    aggression: float = 0.5        # 0 = passive, 1 = hyper-aggressive
    pace: float = 0.5              # 0 = slow / deliberate, 1 = hurry-up
    risk_tolerance: float = 0.5    # 0 = conservative, 1 = reckless
    adaptability: float = 0.5      # 0 = rigid, 1 = constantly adjusting
    tendency_entropy: float = 0.5  # 0 = predictable, 1 = chaotic
    blitz_rate: float = 0.0        # fraction of plays involving blitz / rush
    play_type_ratio: float = 0.5   # 0 = all run, 1 = all pass
    fourth_down_go_rate: float = 0.0
    sample_size: int = 0

    @property
    def vector(self) -> list[float]:
        return [
            self.aggression,
            self.pace,
            self.risk_tolerance,
            self.adaptability,
            self.tendency_entropy,
            self.blitz_rate,
            self.play_type_ratio,
            self.fourth_down_go_rate,
        ]


@dataclass
class OpponentRecord:
    """Canonical opponent entity."""

    opponent_id: str
    gamertags: list[str] = field(default_factory=list)
    platform_ids: list[str] = field(default_factory=list)
    titles: list[str] = field(default_factory=list)
    fingerprint: BehavioralFingerprint = field(default_factory=BehavioralFingerprint)
    encounter_count: int = 0
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    merged_from: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# In-memory store (will be replaced with DB)
# ---------------------------------------------------------------------------

_opponent_store: dict[str, OpponentRecord] = {}

# Gamertag -> opponent_id index
_gamertag_index: dict[str, str] = {}

# Platform ID -> opponent_id index
_platform_index: dict[str, str] = {}


def _reset_store() -> None:
    """Clear all stores (test helper)."""
    _opponent_store.clear()
    _gamertag_index.clear()
    _platform_index.clear()


# ---------------------------------------------------------------------------
# Fingerprinting
# ---------------------------------------------------------------------------

_EMA_ALPHA = 0.25  # smoothing factor for fingerprint updates


def get_behavioral_fingerprint(opponent_data: dict[str, Any]) -> BehavioralFingerprint:
    """Generate a behavioral fingerprint from raw play-pattern data.

    ``opponent_data`` should contain keys like ``plays``, ``sessions``, or
    pre-aggregated stats.  The function normalises everything to 0-1 and
    builds the fingerprint vector.
    """
    plays: list[dict] = opponent_data.get("plays", [])
    sessions: list[dict] = opponent_data.get("sessions", [])
    stats: dict = opponent_data.get("stats", {})

    sample = len(plays) or len(sessions) or 1
    fp = BehavioralFingerprint(sample_size=sample)

    # --- Aggression: ratio of aggressive/blitz actions to total ---
    aggressive_count = sum(
        1 for p in plays if p.get("tag") in ("blitz", "aggressive", "press", "attack")
    )
    fp.aggression = min(aggressive_count / max(sample, 1), 1.0)

    # --- Pace: average snap-to-play time (lower = faster) ---
    snap_times = [p["snap_time"] for p in plays if "snap_time" in p]
    if snap_times:
        avg_snap = sum(snap_times) / len(snap_times)
        # Normalise: <10s → fast (1.0), >25s → slow (0.0)
        fp.pace = max(0.0, min(1.0, 1.0 - (avg_snap - 10.0) / 15.0))

    # --- Risk tolerance ---
    fourth_downs = [p for p in plays if p.get("down") == 4]
    go_for_it = [p for p in fourth_downs if p.get("decision") == "go"]
    if fourth_downs:
        fp.fourth_down_go_rate = len(go_for_it) / len(fourth_downs)
    fp.risk_tolerance = stats.get("risk_tolerance", fp.fourth_down_go_rate)

    # --- Adaptability: how often scheme/formation changes between drives ---
    schemes = [s.get("scheme") for s in sessions if "scheme" in s]
    if len(schemes) > 1:
        changes = sum(1 for a, b in zip(schemes, schemes[1:]) if a != b)
        fp.adaptability = min(changes / max(len(schemes) - 1, 1), 1.0)

    # --- Tendency entropy (Shannon) ---
    play_types = [p.get("type") for p in plays if "type" in p]
    if play_types:
        fp.tendency_entropy = _shannon_entropy(play_types)

    # --- Play type ratio (run vs pass) ---
    pass_count = sum(1 for t in play_types if t and "pass" in t.lower())
    if play_types:
        fp.play_type_ratio = pass_count / len(play_types)

    # --- Blitz rate ---
    blitzes = sum(1 for p in plays if p.get("is_blitz"))
    fp.blitz_rate = blitzes / max(sample, 1)

    logger.debug("fingerprint built", extra={"sample_size": sample, "aggression": fp.aggression})
    return fp


def _shannon_entropy(labels: list[str]) -> float:
    """Normalised Shannon entropy of a label list (0 = uniform, 1 = max)."""
    from collections import Counter

    counts = Counter(labels)
    total = sum(counts.values())
    if total == 0 or len(counts) <= 1:
        return 0.0
    probs = [c / total for c in counts.values()]
    raw = -sum(p * math.log2(p) for p in probs if p > 0)
    max_ent = math.log2(len(counts))
    return raw / max_ent if max_ent > 0 else 0.0


# ---------------------------------------------------------------------------
# Similarity
# ---------------------------------------------------------------------------

def calculate_similarity(
    fingerprint_a: BehavioralFingerprint,
    fingerprint_b: BehavioralFingerprint,
) -> float:
    """Cosine-similarity between two fingerprint vectors, returned as 0-1 score."""
    va = fingerprint_a.vector
    vb = fingerprint_b.vector
    dot = sum(a * b for a, b in zip(va, vb))
    mag_a = math.sqrt(sum(a * a for a in va)) or 1e-9
    mag_b = math.sqrt(sum(b * b for b in vb)) or 1e-9
    similarity = dot / (mag_a * mag_b)
    return max(0.0, min(1.0, similarity))


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

_FINGERPRINT_MERGE_THRESHOLD = 0.85  # similarity above which we auto-suggest merge
_GAMERTAG_EXACT_WEIGHT = 0.6
_FINGERPRINT_WEIGHT = 0.4


def resolve_opponent(identifier: str, title: str) -> OpponentRecord:
    """Resolve an opponent by gamertag or platform ID, creating if needed.

    Resolution order:
    1. Exact gamertag match.
    2. Platform ID match.
    3. Behavioural-fingerprint similarity against existing records.
    4. Create new record if no match found.
    """
    normalised = identifier.strip().lower()

    # 1 — exact gamertag lookup
    if normalised in _gamertag_index:
        opp_id = _gamertag_index[normalised]
        record = _opponent_store[opp_id]
        if title not in record.titles:
            record.titles.append(title)
        record.last_seen = datetime.now(timezone.utc)
        logger.info("resolved opponent via gamertag", extra={"opponent_id": opp_id})
        return record

    # 2 — platform ID lookup
    if normalised in _platform_index:
        opp_id = _platform_index[normalised]
        record = _opponent_store[opp_id]
        if title not in record.titles:
            record.titles.append(title)
        record.last_seen = datetime.now(timezone.utc)
        logger.info("resolved opponent via platform ID", extra={"opponent_id": opp_id})
        return record

    # 3 — create new record
    opp_id = _generate_opponent_id(normalised)
    record = OpponentRecord(
        opponent_id=opp_id,
        gamertags=[normalised],
        titles=[title],
    )
    _opponent_store[opp_id] = record
    _gamertag_index[normalised] = opp_id
    logger.info("created new opponent record", extra={"opponent_id": opp_id, "gamertag": normalised})
    return record


def merge_duplicates(opponent_ids: list[str]) -> OpponentRecord:
    """Merge multiple opponent records into one canonical record.

    The first ID in the list becomes the canonical record.  All others
    are absorbed: their gamertags, platform IDs, encounters, and
    fingerprints are combined, and their old IDs are redirected.
    """
    if len(opponent_ids) < 2:
        raise ValueError("Need at least two opponent IDs to merge")

    valid = [oid for oid in opponent_ids if oid in _opponent_store]
    if len(valid) < 2:
        raise ValueError(f"Only {len(valid)} of {len(opponent_ids)} IDs found in store")

    canonical = _opponent_store[valid[0]]
    logger.info("merging opponents", extra={"canonical": valid[0], "absorbed": valid[1:]})

    for oid in valid[1:]:
        other = _opponent_store[oid]

        # Merge gamertags
        for gt in other.gamertags:
            if gt not in canonical.gamertags:
                canonical.gamertags.append(gt)
            _gamertag_index[gt] = canonical.opponent_id

        # Merge platform IDs
        for pid in other.platform_ids:
            if pid not in canonical.platform_ids:
                canonical.platform_ids.append(pid)
            _platform_index[pid] = canonical.opponent_id

        # Merge titles
        for t in other.titles:
            if t not in canonical.titles:
                canonical.titles.append(t)

        # Combine encounter counts
        canonical.encounter_count += other.encounter_count

        # Keep earliest first_seen, latest last_seen
        if other.first_seen < canonical.first_seen:
            canonical.first_seen = other.first_seen
        if other.last_seen > canonical.last_seen:
            canonical.last_seen = other.last_seen

        # Weighted-average fingerprints
        canonical.fingerprint = _merge_fingerprints(
            canonical.fingerprint, other.fingerprint
        )

        canonical.merged_from.append(oid)
        del _opponent_store[oid]

    return canonical


def _merge_fingerprints(
    a: BehavioralFingerprint, b: BehavioralFingerprint
) -> BehavioralFingerprint:
    """Sample-weighted average of two fingerprints."""
    total = a.sample_size + b.sample_size or 1
    wa = a.sample_size / total
    wb = b.sample_size / total
    return BehavioralFingerprint(
        aggression=wa * a.aggression + wb * b.aggression,
        pace=wa * a.pace + wb * b.pace,
        risk_tolerance=wa * a.risk_tolerance + wb * b.risk_tolerance,
        adaptability=wa * a.adaptability + wb * b.adaptability,
        tendency_entropy=wa * a.tendency_entropy + wb * b.tendency_entropy,
        blitz_rate=wa * a.blitz_rate + wb * b.blitz_rate,
        play_type_ratio=wa * a.play_type_ratio + wb * b.play_type_ratio,
        fourth_down_go_rate=wa * a.fourth_down_go_rate + wb * b.fourth_down_go_rate,
        sample_size=total,
    )


def _generate_opponent_id(seed: str) -> str:
    """Deterministic short ID from a seed string."""
    digest = hashlib.sha256(seed.encode()).hexdigest()[:12]
    return f"opp_{digest}"

"""CommunityIntel — community meta aggregation, data contribution, rankings, and opponent seeding.

Aggregates community-contributed meta data, manages data contribution pipelines,
provides community rankings, and seeds opponent scouting databases.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from app.schemas.community import (
    CommunityContribution,
    CommunityMeta,
    CommunityRanking,
    CommunityRankingsResponse,
    ContributionResult,
    OpponentSeed,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

_meta_store: dict[str, dict[str, Any]] = {}
_contributions: list[CommunityContribution] = []
_rankings: dict[str, list[CommunityRanking]] = defaultdict(list)
_opponent_seeds: dict[str, dict[str, OpponentSeed]] = defaultdict(dict)
_user_reputation: dict[str, float] = defaultdict(lambda: 0.5)

# ---------------------------------------------------------------------------
# Reputation thresholds
# ---------------------------------------------------------------------------

_MIN_REPUTATION_CONTRIBUTE = 0.2
_REPUTATION_GAIN_PER_CONTRIBUTION = 0.02
_REPUTATION_DECAY_ON_BAD_DATA = 0.05

# ---------------------------------------------------------------------------
# Tier ELO boundaries
# ---------------------------------------------------------------------------

_ELO_TIERS: list[tuple[int, str]] = [
    (2000, "champion"),
    (1700, "diamond"),
    (1400, "platinum"),
    (1200, "gold"),
    (1000, "silver"),
    (0, "bronze"),
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _elo_to_tier(elo: float) -> str:
    for threshold, tier in _ELO_TIERS:
        if elo >= threshold:
            return tier
    return "bronze"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_community_meta(title: str, patch_version: str = "latest") -> CommunityMeta:
    """Aggregate community-sourced meta data for a title.

    Compiles strategy frequencies, trending data, and sample sizes
    from community contributions to produce a meta snapshot.
    """
    title_contributions = [c for c in _contributions if c.title == title and c.data_type == "strategy"]

    strategy_counts: dict[str, int] = defaultdict(int)
    for contrib in title_contributions:
        strategy = contrib.payload.get("strategy", "unknown")
        strategy_counts[strategy] += 1

    # Sort by frequency
    sorted_strategies = sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True)
    top = [{"strategy": s, "frequency": c} for s, c in sorted_strategies[:10]]

    # Trending: strategies with increasing recent contributions
    recent = [c for c in title_contributions[-50:]]
    recent_counts: dict[str, int] = defaultdict(int)
    for c in recent:
        recent_counts[c.payload.get("strategy", "unknown")] += 1

    older = [c for c in title_contributions[:-50]]
    older_counts: dict[str, int] = defaultdict(int)
    for c in older:
        older_counts[c.payload.get("strategy", "unknown")] += 1

    trending_up = [
        s for s in recent_counts
        if recent_counts[s] > older_counts.get(s, 0)
    ][:5]
    trending_down = [
        s for s in older_counts
        if older_counts[s] > recent_counts.get(s, 0)
    ][:5]

    return CommunityMeta(
        title=title,
        patch_version=patch_version,
        top_strategies=top,
        trending_up=trending_up,
        trending_down=trending_down,
        sample_size=len(title_contributions),
        last_updated=_now_iso(),
    )


def contribute_data(contribution: CommunityContribution) -> ContributionResult:
    """Submit a data contribution from a community member.

    Validates the contribution, checks user reputation, and either
    accepts or rejects the data point.
    """
    user_rep = _user_reputation[contribution.user_id]

    if user_rep < _MIN_REPUTATION_CONTRIBUTE:
        return ContributionResult(
            accepted=False,
            message=f"Reputation too low ({user_rep:.2f}). Minimum required: {_MIN_REPUTATION_CONTRIBUTE}.",
        )

    # Validate payload
    if not contribution.payload:
        _user_reputation[contribution.user_id] = max(0, user_rep - _REPUTATION_DECAY_ON_BAD_DATA)
        return ContributionResult(
            accepted=False,
            message="Empty payload — contribution rejected.",
            reputation_delta=-_REPUTATION_DECAY_ON_BAD_DATA,
        )

    # Validate data type
    valid_types = {"strategy", "match_result", "opponent_data"}
    if contribution.data_type not in valid_types:
        return ContributionResult(
            accepted=False,
            message=f"Invalid data type. Must be one of: {valid_types}.",
        )

    # Accept contribution
    contribution.timestamp = _now_iso()
    contribution.reputation_score = user_rep
    _contributions.append(contribution)

    _user_reputation[contribution.user_id] = min(1.0, user_rep + _REPUTATION_GAIN_PER_CONTRIBUTION)
    contrib_id = f"contrib_{uuid.uuid4().hex[:12]}"

    logger.info(
        "Community contribution accepted: user=%s title=%s type=%s",
        contribution.user_id, contribution.title, contribution.data_type,
    )

    return ContributionResult(
        accepted=True,
        contribution_id=contrib_id,
        reputation_delta=_REPUTATION_GAIN_PER_CONTRIBUTION,
        message="Contribution accepted. Thank you for improving the community meta.",
    )


def get_community_rankings(
    title: str,
    user_id: str | None = None,
    limit: int = 50,
) -> CommunityRankingsResponse:
    """Get community rankings for a title.

    Returns the top players by ELO rating, with the requesting user's
    rank included if provided.
    """
    title_rankings = _rankings.get(title, [])

    if not title_rankings:
        # Generate sample rankings from contributions
        user_wins: dict[str, int] = defaultdict(int)
        user_losses: dict[str, int] = defaultdict(int)
        for c in _contributions:
            if c.title == title and c.data_type == "match_result":
                uid = c.user_id
                if c.payload.get("result") == "win":
                    user_wins[uid] += 1
                else:
                    user_losses[uid] += 1

        rankings: list[CommunityRanking] = []
        for uid in set(list(user_wins.keys()) + list(user_losses.keys())):
            wins = user_wins[uid]
            losses = user_losses[uid]
            total = wins + losses
            wr = wins / max(total, 1)
            elo = 1000 + (wins - losses) * 30
            rankings.append(CommunityRanking(
                user_id=uid, title=title, rank=0, elo=elo,
                wins=wins, losses=losses, win_rate=round(wr, 3),
                tier=_elo_to_tier(elo),
            ))

        rankings.sort(key=lambda r: r.elo, reverse=True)
        for i, r in enumerate(rankings):
            r.rank = i + 1

        _rankings[title] = rankings
        title_rankings = rankings

    your_rank = None
    if user_id:
        match = next((r for r in title_rankings if r.user_id == user_id), None)
        if match:
            your_rank = match.rank

    return CommunityRankingsResponse(
        title=title,
        rankings=title_rankings[:limit],
        total_players=len(title_rankings),
        your_rank=your_rank,
    )


def seed_opponent_data(
    title: str,
    opponent_id: str,
    tendencies: dict[str, Any],
    archetype: str = "unknown",
) -> OpponentSeed:
    """Seed or update opponent scouting data from community contributions.

    Merges new tendency data with existing observations, increasing
    confidence with each additional data point.
    """
    existing = _opponent_seeds[title].get(opponent_id)

    if existing:
        # Merge tendencies with EMA blending
        for key, value in tendencies.items():
            if key in existing.tendencies and isinstance(value, (int, float)):
                existing.tendencies[key] = round(
                    existing.tendencies[key] * 0.7 + value * 0.3, 4
                )
            else:
                existing.tendencies[key] = value
        existing.sample_size += 1
        existing.confidence = min(0.95, existing.confidence + 0.05)
        existing.last_seen = _now_iso()
        if archetype != "unknown":
            existing.archetype = archetype
        _opponent_seeds[title][opponent_id] = existing
        return existing

    seed = OpponentSeed(
        opponent_id=opponent_id,
        title=title,
        archetype=archetype,
        tendencies=tendencies,
        sample_size=1,
        confidence=0.30,
        last_seen=_now_iso(),
    )
    _opponent_seeds[title][opponent_id] = seed

    logger.info("Opponent seeded: title=%s opponent=%s archetype=%s", title, opponent_id, archetype)
    return seed

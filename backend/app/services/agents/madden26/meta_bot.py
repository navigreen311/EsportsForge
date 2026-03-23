"""MetaBot — Weekly meta scanning, strategy rating, and exploit detection for Madden 26."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.schemas.madden26.gameplan import (
    MetaExploit,
    MetaRating,
    MetaRatingValue,
    MetaReport,
)


# ---------------------------------------------------------------------------
# Static meta knowledge (would be fed by real-time data in production)
# ---------------------------------------------------------------------------

_CURRENT_PATCH = "1.06"

_META_STATE: dict[str, list[str]] = {
    "top_strategies": [
        "Gun Bunch TE — Mesh/Drive combos",
        "Cover 2 Man with user LB in the middle",
        "Pistol RPO heavy with mobile QB",
        "Nickel 3-3-5 Wide blitz packages",
    ],
    "rising_strategies": [
        "Singleback Wing — outside zone + PA",
        "Tampa 2 with aggressive flats",
        "QB scramble chains from Gun Spread",
    ],
    "declining_strategies": [
        "Four Verticals spam from Gun Trips",
        "Nano blitzes from 3-4 Odd",
        "Dollar formation cheese plays",
    ],
}

_EXPLOITS: list[dict[str, str]] = [
    {
        "name": "Bunch TE Mesh Crosser",
        "description": (
            "Mesh concept from Gun Bunch TE creates natural rub routes that "
            "consistently beat man coverage. The crosser underneath is nearly "
            "unguardable without a manual user adjustment."
        ),
        "counter": "User the MLB over the middle, switch to Cover 3 Match",
        "time_remaining": "Likely patched in 1.07",
        "risk_level": "high",
    },
    {
        "name": "Nickel 3-3-5 Wide Edge Heat",
        "description": (
            "Overloading the edge from Nickel 3-3-5 Wide sends unblockable "
            "pressure from the field side when the offense has no TE."
        ),
        "counter": "Slide protection to the field, keep RB in to block",
        "time_remaining": "2-3 weeks",
        "risk_level": "medium",
    },
    {
        "name": "RPO Glitch — Read Option + Slant",
        "description": (
            "Specific RPO from Pistol where the slant animation clips through "
            "the zone defender's coverage assignment."
        ),
        "counter": "User the hook zone defender manually",
        "time_remaining": "Expected fix in next title update",
        "risk_level": "medium",
    },
]

# Strategy ratings baseline
_STRATEGY_RATINGS: dict[str, tuple[MetaRatingValue, str]] = {
    "gun_bunch": (MetaRatingValue.EXPLOIT, "Gun Bunch concepts are dominant this patch."),
    "cover_2_man": (MetaRatingValue.STRONG, "Cover 2 Man is a top defensive scheme."),
    "rpo_heavy": (MetaRatingValue.STRONG, "RPO schemes remain effective with mobile QBs."),
    "four_verticals": (MetaRatingValue.COUNTERED, "Four Verticals is heavily scouted and countered."),
    "nano_blitz": (MetaRatingValue.EXPIRED, "Most nano blitzes were patched in 1.05."),
    "west_coast": (MetaRatingValue.STRONG, "West Coast timing routes are consistent."),
    "spread": (MetaRatingValue.STRONG, "Spread creates favorable matchups in space."),
    "run_power": (MetaRatingValue.NEUTRAL, "Power run is matchup-dependent."),
    "air_raid": (MetaRatingValue.NEUTRAL, "Air Raid is viable but predictable at high level."),
}


class MetaBot:
    """
    MetaBot for Madden 26.

    Tracks the competitive meta, rates strategies against it, detects
    exploits, and checks for staleness after patches.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def scan_weekly_meta(self, title: str = "madden26") -> MetaReport:
        """Return the current meta state as a weekly report."""
        exploits = [
            MetaExploit(
                name=e["name"],
                description=e["description"],
                counter=e.get("counter"),
                time_remaining=e.get("time_remaining"),
                risk_level=e.get("risk_level", "medium"),
            )
            for e in _EXPLOITS
        ]

        return MetaReport(
            title=title,
            patch_version=_CURRENT_PATCH,
            report_date=datetime.now(timezone.utc).date().isoformat(),
            top_strategies=_META_STATE["top_strategies"],
            rising_strategies=_META_STATE["rising_strategies"],
            declining_strategies=_META_STATE["declining_strategies"],
            exploits=exploits,
            meta_summary=(
                f"Madden 26 patch {_CURRENT_PATCH} meta is dominated by Gun Bunch passing "
                f"concepts and aggressive Nickel blitz packages. RPO schemes with mobile "
                f"QBs remain strong. Four Verticals spam and nano blitzes are declining. "
                f"Expect a shift toward outside zone running as the counter meta develops."
            ),
        )

    async def rate_strategy(self, strategy: str) -> MetaRating:
        """Rate a strategy against the current meta."""
        key = strategy.lower().replace(" ", "_").replace("-", "_")

        if key in _STRATEGY_RATINGS:
            rating, explanation = _STRATEGY_RATINGS[key]
        else:
            # Unknown strategy — rate as neutral with lower confidence
            rating = MetaRatingValue.NEUTRAL
            explanation = f"Strategy '{strategy}' is not tracked in the current meta database."

        confidence = 0.85 if key in _STRATEGY_RATINGS else 0.45
        adjustments: list[str] = []

        if rating == MetaRatingValue.COUNTERED:
            adjustments.append("Consider switching to a rising strategy.")
            adjustments.append("Mix in concepts from a different scheme to stay unpredictable.")
        elif rating == MetaRatingValue.EXPIRED:
            adjustments.append("This strategy is no longer viable. Switch immediately.")
        elif rating == MetaRatingValue.NEUTRAL:
            adjustments.append("Can work but requires precise execution and reads.")

        return MetaRating(
            strategy=strategy,
            rating=rating,
            explanation=explanation,
            confidence=confidence,
            suggested_adjustments=adjustments,
        )

    async def get_meta_exploits(self) -> list[MetaExploit]:
        """Return currently exploitable strategies."""
        return [
            MetaExploit(
                name=e["name"],
                description=e["description"],
                counter=e.get("counter"),
                time_remaining=e.get("time_remaining"),
                risk_level=e.get("risk_level", "medium"),
            )
            for e in _EXPLOITS
        ]

    async def check_staleness(
        self, strategy: str, patch_version: Optional[str] = None
    ) -> bool:
        """Check if a strategy is stale (expired or countered) after a patch."""
        effective_patch = patch_version or _CURRENT_PATCH
        rating = await self.rate_strategy(strategy)

        # If explicitly expired or countered, it's stale
        if rating.rating in (MetaRatingValue.EXPIRED, MetaRatingValue.COUNTERED):
            return True

        # Check if the strategy appears in declining list
        declining_lower = [s.lower() for s in _META_STATE["declining_strategies"]]
        strategy_lower = strategy.lower()
        for d in declining_lower:
            if strategy_lower in d:
                return True

        return False

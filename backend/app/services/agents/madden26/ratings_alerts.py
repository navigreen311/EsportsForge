"""Ratings Update Impact Alerts — monitor patch notes for rating changes
and auto-adjust gameplan recommendations.

Analyzes EA patch notes for player rating changes, identifies which user
gameplans are affected, generates impact reports, and optionally auto-adjusts
recommendations to stay current with the meta.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory stores (replaced by DB in production)
# ---------------------------------------------------------------------------

_impact_reports: dict[str, dict[str, Any]] = {}  # report_id -> report
_user_adjustments: dict[str, list[dict[str, Any]]] = {}  # user_id -> adjustments


def reset_store() -> None:
    """Clear all in-memory state (for testing)."""
    _impact_reports.clear()
    _user_adjustments.clear()


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

def check_patch_impact(patch_notes: dict[str, Any]) -> dict[str, Any]:
    """Analyze patch notes for rating changes that affect gameplay.

    Parameters
    ----------
    patch_notes : dict
        Must contain ``patch_version`` (str) and ``changes`` (list of dicts
        with ``player_name``, ``attribute``, ``old_value``, ``new_value``).

    Returns
    -------
    dict with ``patch_version``, ``total_changes``, ``significant_changes``
    (abs delta >= 3), and ``rating_changes`` list.
    """
    patch_version = patch_notes.get("patch_version", "unknown")
    raw_changes: list[dict[str, Any]] = patch_notes.get("changes", [])

    rating_changes: list[dict[str, Any]] = []
    significant: list[dict[str, Any]] = []

    for change in raw_changes:
        old_val = change.get("old_value", 0)
        new_val = change.get("new_value", 0)
        delta = new_val - old_val

        entry = {
            "player_name": change.get("player_name", "Unknown"),
            "attribute": change.get("attribute", "overall"),
            "old_value": old_val,
            "new_value": new_val,
            "delta": delta,
            "direction": "buff" if delta > 0 else ("nerf" if delta < 0 else "unchanged"),
        }
        rating_changes.append(entry)

        if abs(delta) >= 3:
            significant.append(entry)

    result = {
        "patch_version": patch_version,
        "total_changes": len(rating_changes),
        "significant_changes": significant,
        "rating_changes": rating_changes,
        "analyzed_at": _now().isoformat(),
    }

    logger.info(
        "Patch %s analyzed: %d changes, %d significant",
        patch_version,
        len(rating_changes),
        len(significant),
    )
    return result


def get_affected_gameplans(
    user_id: str, changes: list[dict[str, Any]]
) -> dict[str, Any]:
    """Identify which of a user's gameplans are affected by rating changes.

    Parameters
    ----------
    user_id : str
        The user whose gameplans to check.
    changes : list[dict]
        List of rating change dicts (from ``check_patch_impact``).

    Returns
    -------
    dict with ``user_id``, ``affected_gameplans``, and ``total_affected``.
    """
    affected_players = {c.get("player_name", "").lower() for c in changes}

    # Stub: in production this queries the gameplan store
    # For now, generate placeholder affected gameplans
    affected: list[dict[str, Any]] = []
    for i, player in enumerate(list(affected_players)[:5]):
        affected.append({
            "gameplan_id": f"gp-{user_id}-{i}",
            "gameplan_name": f"Gameplan {i + 1}",
            "affected_player": player,
            "impact_level": "high" if i < 2 else "medium",
            "reason": f"Player '{player}' rating changed",
        })

    result = {
        "user_id": user_id,
        "affected_gameplans": affected,
        "total_affected": len(affected),
        "checked_at": _now().isoformat(),
    }

    logger.info(
        "User %s: %d gameplans affected by rating changes",
        user_id,
        len(affected),
    )
    return result


def generate_impact_report(changes: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate a detailed impact report from rating changes.

    Parameters
    ----------
    changes : list[dict]
        Rating change entries (from ``check_patch_impact``).

    Returns
    -------
    dict with ``report_id``, ``summary``, ``buffs``, ``nerfs``,
    ``position_impact``, and ``meta_implications``.
    """
    report_id = _generate_id()

    buffs = [c for c in changes if c.get("delta", 0) > 0]
    nerfs = [c for c in changes if c.get("delta", 0) < 0]

    # Group by position/attribute for meta implications
    position_impact: dict[str, int] = {}
    for c in changes:
        attr = c.get("attribute", "overall")
        position_impact[attr] = position_impact.get(attr, 0) + 1

    # Determine meta implications
    meta_implications: list[str] = []
    if len(buffs) > len(nerfs):
        meta_implications.append("Overall power level increase — expect more aggressive metas")
    elif len(nerfs) > len(buffs):
        meta_implications.append("Overall power level decrease — defensive metas may emerge")
    if any(abs(c.get("delta", 0)) >= 5 for c in changes):
        meta_implications.append("Major rating swings detected — meta shift likely")

    report = {
        "report_id": report_id,
        "summary": f"{len(changes)} rating changes: {len(buffs)} buffs, {len(nerfs)} nerfs",
        "total_changes": len(changes),
        "buffs": buffs,
        "nerfs": nerfs,
        "unchanged": [c for c in changes if c.get("delta", 0) == 0],
        "position_impact": position_impact,
        "meta_implications": meta_implications,
        "generated_at": _now().isoformat(),
    }

    _impact_reports[report_id] = report

    logger.info("Impact report %s generated: %d changes", report_id, len(changes))
    return report


def auto_adjust_recommendations(
    user_id: str, changes: list[dict[str, Any]]
) -> dict[str, Any]:
    """Auto-adjust gameplan recommendations based on rating changes.

    Parameters
    ----------
    user_id : str
        The user whose recommendations to adjust.
    changes : list[dict]
        Rating change entries.

    Returns
    -------
    dict with ``user_id``, ``adjustments``, and ``total_adjustments``.
    """
    adjustments: list[dict[str, Any]] = []

    for change in changes:
        delta = change.get("delta", 0)
        if abs(delta) < 2:
            continue  # Skip minor changes

        player = change.get("player_name", "Unknown")
        attr = change.get("attribute", "overall")

        adjustment: dict[str, Any] = {
            "adjustment_id": _generate_id(),
            "player_name": player,
            "attribute": attr,
            "delta": delta,
            "recommendation": "",
            "priority": "high" if abs(delta) >= 5 else "medium",
        }

        if delta > 0:
            adjustment["recommendation"] = (
                f"Consider featuring {player} more — {attr} boosted by +{delta}"
            )
        else:
            adjustment["recommendation"] = (
                f"Reduce reliance on {player} — {attr} dropped by {delta}"
            )

        adjustments.append(adjustment)

    # Store adjustments
    if user_id not in _user_adjustments:
        _user_adjustments[user_id] = []
    _user_adjustments[user_id].extend(adjustments)

    result = {
        "user_id": user_id,
        "adjustments": adjustments,
        "total_adjustments": len(adjustments),
        "applied_at": _now().isoformat(),
    }

    logger.info(
        "Auto-adjusted %d recommendations for user %s",
        len(adjustments),
        user_id,
    )
    return result

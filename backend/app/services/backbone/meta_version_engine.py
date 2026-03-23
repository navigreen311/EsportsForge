"""MetaVersion Engine — tracks meta shifts across game patches.

Snapshots the current meta state per patch, stamps recommendations with
version info, and detects when advice becomes stale after a new patch.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from app.schemas.film import (
    AdviceStatus,
    MetaSnapshot,
    MetaVersionStamp,
    PatchVersion,
    StaleAdviceAlert,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory stores (replaced by DB in production)
# ---------------------------------------------------------------------------

# title -> patch_version -> MetaSnapshot
_snapshots: dict[str, dict[str, MetaSnapshot]] = defaultdict(dict)
# title -> [PatchVersion] ordered by release
_patch_history: dict[str, list[PatchVersion]] = defaultdict(list)
# recommendation_id -> MetaVersionStamp
_stamps: dict[str, MetaVersionStamp] = {}


def reset_store() -> None:
    """Clear all in-memory state (for testing)."""
    _snapshots.clear()
    _patch_history.clear()
    _stamps.clear()


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

def create_snapshot(title: str, patch_version: str, **kwargs: Any) -> MetaSnapshot:
    """Freeze the current meta state for *title* at *patch_version*.

    Optional keyword args are forwarded to MetaSnapshot (top_strategies,
    tier_list, meta_notes).
    """
    snapshot = MetaSnapshot(
        title=title,
        patch_version=patch_version,
        top_strategies=kwargs.get("top_strategies", []),
        tier_list=kwargs.get("tier_list", {}),
        meta_notes=kwargs.get("meta_notes", ""),
        snapshot_at=_now(),
    )
    _snapshots[title][patch_version] = snapshot

    # Record the patch if we haven't seen it yet
    known_versions = {p.version for p in _patch_history[title]}
    if patch_version not in known_versions:
        _patch_history[title].append(
            PatchVersion(
                title=title,
                version=patch_version,
                released_at=_now(),
                changelog_notes=kwargs.get("changelog_notes", []),
            )
        )

    logger.info("Created meta snapshot for %s @ patch %s", title, patch_version)
    return snapshot


def get_snapshot(title: str, patch_version: str) -> MetaSnapshot:
    """Retrieve a historical meta snapshot."""
    title_snaps = _snapshots.get(title, {})
    snapshot = title_snaps.get(patch_version)
    if snapshot is None:
        raise ValueError(
            f"No meta snapshot for {title} @ patch {patch_version}"
        )
    return snapshot


def stamp_recommendation(
    recommendation: str, patch_version: str, title: str
) -> MetaVersionStamp:
    """Attach a version stamp to a recommendation so we can track freshness."""
    rec_id = _generate_id()
    stamp = MetaVersionStamp(
        recommendation_id=rec_id,
        recommendation_text=recommendation,
        patch_version=patch_version,
        title=title,
        status=AdviceStatus.ACTIVE,
        stamped_at=_now(),
    )
    _stamps[rec_id] = stamp
    logger.info("Stamped recommendation %s for %s @ %s", rec_id, title, patch_version)
    return stamp


def detect_stale_advice(
    title: str, current_patch: str
) -> list[StaleAdviceAlert]:
    """Find recommendations that may be stale because a newer patch exists."""
    alerts: list[StaleAdviceAlert] = []
    for stamp in _stamps.values():
        if stamp.title != title:
            continue
        if stamp.status == AdviceStatus.EXPIRED:
            continue
        if stamp.patch_version != current_patch:
            alerts.append(
                StaleAdviceAlert(
                    recommendation_id=stamp.recommendation_id,
                    recommendation_text=stamp.recommendation_text,
                    stamped_patch=stamp.patch_version,
                    current_patch=current_patch,
                    title=title,
                    reason=(
                        f"Recommendation was created for patch {stamp.patch_version} "
                        f"but current patch is {current_patch}"
                    ),
                    detected_at=_now(),
                )
            )
    logger.info(
        "Detected %d stale advice alerts for %s (current patch %s)",
        len(alerts), title, current_patch,
    )
    return alerts


def auto_expire_stale(title: str, new_patch: str) -> list[MetaVersionStamp]:
    """Mark all recommendations from older patches as expired."""
    expired: list[MetaVersionStamp] = []
    for stamp in _stamps.values():
        if stamp.title != title:
            continue
        if stamp.patch_version != new_patch and stamp.status != AdviceStatus.EXPIRED:
            stamp.status = AdviceStatus.EXPIRED
            expired.append(stamp)
    logger.info(
        "Auto-expired %d recommendations for %s after patch %s",
        len(expired), title, new_patch,
    )
    return expired


def get_patch_changelog(
    title: str, from_patch: str, to_patch: str
) -> dict[str, Any]:
    """Return what changed between two patches for a given title."""
    patches = _patch_history.get(title, [])
    versions = [p.version for p in patches]

    if from_patch not in versions or to_patch not in versions:
        raise ValueError(
            f"Patch range {from_patch}→{to_patch} not fully found for {title}. "
            f"Known patches: {versions}"
        )

    from_idx = versions.index(from_patch)
    to_idx = versions.index(to_patch)

    if from_idx >= to_idx:
        raise ValueError(
            f"from_patch ({from_patch}) must precede to_patch ({to_patch})"
        )

    intermediate = patches[from_idx + 1 : to_idx + 1]
    all_notes: list[str] = []
    patch_list: list[dict[str, Any]] = []
    for p in intermediate:
        all_notes.extend(p.changelog_notes)
        patch_list.append({
            "version": p.version,
            "released_at": p.released_at.isoformat(),
            "notes": p.changelog_notes,
        })

    from_snap = _snapshots.get(title, {}).get(from_patch)
    to_snap = _snapshots.get(title, {}).get(to_patch)

    return {
        "title": title,
        "from_patch": from_patch,
        "to_patch": to_patch,
        "patches": patch_list,
        "combined_notes": all_notes,
        "meta_diff": {
            "from_strategies": from_snap.top_strategies if from_snap else [],
            "to_strategies": to_snap.top_strategies if to_snap else [],
        },
    }

"""Pre-generate drill demonstration animations for every (title, drill) pair.

Drill demos are shared across all users (cached by ``f"{title_id}:{drill_type}"``
on AnimaForgeJob with ``user_id="system"``), so warming the cache once means
every user gets instant playback the first time they open a drill brief.

Usage::

    python scripts/pre_generate_drill_animations.py
    python scripts/pre_generate_drill_animations.py --dry-run
    python scripts/pre_generate_drill_animations.py --title madden-26
    python scripts/pre_generate_drill_animations.py --skip-existing

The script imports the project's drill spec table and AnimaForge client, so it
must be run from the repo root with the backend venv active::

    cd backend && ./venv/Scripts/python.exe ../scripts/pre_generate_drill_animations.py

If AnimaForge is offline, the script reports the situation and exits 0 (this is
a maintenance script — never block CI on it).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Make ``backend`` importable when invoked from the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_DIR = _REPO_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("animaforge.pregen")


SYSTEM_USER_ID = "system"


async def _pregen(
    *,
    title_filter: str | None,
    skip_existing: bool,
    dry_run: bool,
) -> int:
    from app.services.animaforge.client import AnimaForgeService
    from app.services.animaforge.drill_spec import (
        DRILL_ANIMATION_SPECS,
        build_drill_animation_spec,
    )

    if not dry_run:
        if not await AnimaForgeService.is_available():
            logger.warning(
                "AnimaForge is offline — nothing to do. Set ANIMAFORGE_API_URL "
                "and re-run, or pass --dry-run to print the plan."
            )
            return 0

    # Optional DB de-dup of already-rendered (title, drill) pairs.
    existing: set[tuple[str, str]] = set()
    if skip_existing and not dry_run:
        try:
            from sqlalchemy import select
            from app.db.base import async_session_factory
            from app.models.animaforge import (
                AnimaForgeJob,
                JOB_TYPE_DRILL,
                STATUS_COMPLETE,
            )

            async with async_session_factory() as db:
                result = await db.execute(
                    select(AnimaForgeJob.title_id, AnimaForgeJob.source_id)
                    .where(
                        AnimaForgeJob.type == JOB_TYPE_DRILL,
                        AnimaForgeJob.status == STATUS_COMPLETE,
                    )
                )
                for title_id, drill_type in result.all():
                    existing.add((title_id, drill_type))
            logger.info("found %d already-complete drill jobs", len(existing))
        except Exception:  # noqa: BLE001
            logger.exception("skip-existing lookup failed — generating all pairs")
            existing.clear()

    submitted = 0
    skipped = 0
    failed = 0

    titles = sorted(DRILL_ANIMATION_SPECS.keys())
    if title_filter:
        if title_filter not in titles:
            logger.error(
                "unknown title %r (known: %s)", title_filter, ", ".join(titles)
            )
            return 1
        titles = [title_filter]

    for title_id in titles:
        drill_types = sorted(DRILL_ANIMATION_SPECS[title_id].keys())
        logger.info(
            "title=%s drills=%d (%s)",
            title_id,
            len(drill_types),
            ", ".join(drill_types),
        )
        for drill_type in drill_types:
            if (title_id, drill_type) in existing:
                logger.info("  skip cached %s/%s", title_id, drill_type)
                skipped += 1
                continue

            spec = build_drill_animation_spec(title_id, drill_type)
            if spec is None:
                logger.warning("  no spec for %s/%s — skipping", title_id, drill_type)
                continue

            if dry_run:
                logger.info(
                    "  [dry-run] would render %s/%s template=%s",
                    title_id,
                    drill_type,
                    spec.get("template"),
                )
                submitted += 1
                continue

            try:
                resp = await AnimaForgeService.request_render(
                    type="drill-demo",
                    title_id=title_id,
                    spec=spec,
                    user_id=SYSTEM_USER_ID,
                )
                logger.info(
                    "  submitted %s/%s job_id=%s",
                    title_id,
                    drill_type,
                    getattr(resp, "job_id", None) or resp.get("job_id"),
                )
                submitted += 1
            except Exception:  # noqa: BLE001
                logger.exception("  request_render failed for %s/%s", title_id, drill_type)
                failed += 1

    logger.info(
        "done — submitted=%d skipped=%d failed=%d", submitted, skipped, failed
    )
    return 0 if failed == 0 else 2


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the plan without submitting any renders",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="restrict to a single title-id (e.g. madden-26)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="skip (title, drill) pairs that already have a complete job in DB",
    )
    args = parser.parse_args()

    # Defensive: load .env if present.
    env_path = _REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

    rc = asyncio.run(
        _pregen(
            title_filter=args.title,
            skip_existing=args.skip_existing,
            dry_run=args.dry_run,
        )
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()

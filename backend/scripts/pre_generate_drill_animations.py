"""Pre-generate every drill demonstration animation after deploy.

Loops over every (title_id, drill_type) pair in
:data:`app.services.animaforge.drill_spec.DRILL_ANIMATION_SPECS` and
either invokes the endpoint logic (default) or hits the live HTTP
endpoint, persisting an AnimaForgeJob row so the demos are ready the
first time players open a drill.

Usage::

    cd backend
    venv/Scripts/python.exe scripts/pre_generate_drill_animations.py
    venv/Scripts/python.exe scripts/pre_generate_drill_animations.py --dry-run

``--dry-run`` prints what would be requested without calling AnimaForge
or persisting any rows.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Make `app...` imports work when running as `python scripts/pre_generate...`.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from sqlalchemy import desc, select  # noqa: E402

from app.db.base import async_session  # noqa: E402
from app.models.animaforge import (  # noqa: E402
    AnimaForgeJob,
    JOB_TYPE_DRILL,
    STATUS_COMPLETE,
    STATUS_PENDING,
)
from app.services.animaforge import (  # noqa: E402
    AnimaForgeService,
    AnimaForgeUnavailable,
)
from app.services.animaforge.drill_spec import (  # noqa: E402
    DRILL_ANIMATION_SPECS,
    build_drill_animation_spec,
)


_SHARED_USER_ID = "system"


def _iter_combos() -> list[tuple[str, str]]:
    """All (title_id, drill_type) pairs declared in the spec table."""
    combos: list[tuple[str, str]] = []
    for title_id, by_drill in DRILL_ANIMATION_SPECS.items():
        for drill_type in by_drill:
            combos.append((title_id, drill_type))
    return combos


async def _existing_complete(session, source_id: str) -> AnimaForgeJob | None:
    return await session.scalar(
        select(AnimaForgeJob)
        .where(AnimaForgeJob.source_id == source_id)
        .where(AnimaForgeJob.type == JOB_TYPE_DRILL)
        .where(AnimaForgeJob.status == STATUS_COMPLETE)
        .order_by(desc(AnimaForgeJob.completed_at))
        .limit(1)
    )


async def _request_one(
    session,
    title_id: str,
    drill_type: str,
    *,
    dry_run: bool,
) -> str:
    """Process a single combo. Returns a one-word status label for the log."""
    source_id = f"{title_id}:{drill_type}"
    spec = build_drill_animation_spec(title_id, drill_type)
    if spec is None:  # defensive — should not happen since we iterate the dict
        return "no-spec"

    if dry_run:
        return "dry-run"

    existing = await _existing_complete(session, source_id)
    if existing is not None:
        return "cached"

    try:
        result = await AnimaForgeService.request_render(
            type=JOB_TYPE_DRILL,
            title_id=title_id,
            spec=spec,
            user_id=_SHARED_USER_ID,
        )
    except AnimaForgeUnavailable as exc:
        return f"unavailable ({exc})"

    job_id = result.get("job_id")
    if not job_id:
        return "no-job-id"

    row = AnimaForgeJob(
        user_id=_SHARED_USER_ID,
        job_id=job_id,
        type=JOB_TYPE_DRILL,
        source_id=source_id,
        title_id=title_id,
        status=STATUS_PENDING,
        spec=spec,
    )
    session.add(row)
    await session.commit()
    return f"submitted ({job_id})"


async def _run(*, dry_run: bool) -> int:
    combos = _iter_combos()
    print(f"[pre-gen] {len(combos)} drill animation combos to process")
    print(f"[pre-gen] dry_run={dry_run}")

    if dry_run:
        for title_id, drill_type in combos:
            print(f"  - {title_id:<12} {drill_type}")
        print(f"[pre-gen] done — would submit {len(combos)} renders")
        return 0

    async with async_session() as session:
        for title_id, drill_type in combos:
            status = await _request_one(
                session, title_id, drill_type, dry_run=False
            )
            print(f"  - {title_id:<12} {drill_type:<22} → {status}")

    print(f"[pre-gen] done — processed {len(combos)} combos")
    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pre-generate AnimaForge drill demonstration videos.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print combos that would be submitted; do not call AnimaForge.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return asyncio.run(_run(dry_run=args.dry_run))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

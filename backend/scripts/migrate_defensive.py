"""Idempotent dev migration — adds defensive strategy schema.

Adds:
  - secret_weapons.side column (default 'offense')
  - defensive_gameplans table
  - defensive_priorities table

Re-running is safe — checks for column/table existence before mutating.

Run:
    backend/venv/Scripts/python.exe backend/scripts/migrate_defensive.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402

from app.db.base import Base, engine  # noqa: E402
import app.models  # noqa: F401, E402  — register all models with Base


async def _has_column(conn, table: str, column: str) -> bool:
    """SQLite-specific column-existence check."""
    rows = (await conn.execute(text(f"PRAGMA table_info({table})"))).all()
    return any(r[1] == column for r in rows)


async def _has_table(conn, table: str) -> bool:
    rows = (
        await conn.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name=:name"
            ),
            {"name": table},
        )
    ).all()
    return len(rows) > 0


async def main() -> None:
    async with engine.begin() as conn:
        # 1. Make sure all currently-known tables exist (idempotent for new ones).
        await conn.run_sync(Base.metadata.create_all)

        # 2. Add `side` column to existing secret_weapons rows if needed.
        if not await _has_column(conn, "secret_weapons", "side"):
            await conn.execute(
                text(
                    "ALTER TABLE secret_weapons "
                    "ADD COLUMN side VARCHAR(16) NOT NULL DEFAULT 'offense'"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_secret_weapons_side "
                    "ON secret_weapons (side)"
                )
            )
            print("[migrate_defensive] added secret_weapons.side column")
        else:
            print("[migrate_defensive] secret_weapons.side already present")

        # 3. Confirm new tables landed (create_all already handled this).
        for table in ("defensive_gameplans", "defensive_priorities"):
            present = await _has_table(conn, table)
            print(f"[migrate_defensive] {table}: {'present' if present else 'MISSING'}")


if __name__ == "__main__":
    asyncio.run(main())

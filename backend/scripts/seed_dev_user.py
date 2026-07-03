"""Seed a local dev user for the Drill Lab live-path E2E.

Idempotent — matched by username; re-running UPDATES the row (and repairs the
email) rather than duplicating. Prints login credentials and a ready access
token.

GOTCHA (why this script exists): the login endpoint validates email with
pydantic ``EmailStr`` (app/schemas/auth.py), which REJECTS domains without a
dot (e.g. ``dev@local``). The seeded email must be RFC-valid — ``dev@example.com``.

Run against a throwaway DB for the E2E (avoids the drifted default
esportsforge.db — see docs/runbooks/local-vision-e2e.md):

    cd backend
    DATABASE_URL="sqlite+aiosqlite:///./e2e_dev.db" \
      .venv/Scripts/python.exe scripts/seed_dev_user.py

No new auth surface — uses the existing hash_password + create_access_token.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

import app.models  # noqa: F401, E402  — register all models with Base
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.db.base import async_session  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402

DEV_USERNAME = "devuser"
DEV_EMAIL = "dev@example.com"  # RFC-valid — EmailStr rejects dot-less domains
DEV_PASSWORD = "devpass123"


async def main() -> None:
    async with async_session() as session:
        existing = (
            await session.execute(select(User).where(User.username == DEV_USERNAME))
        ).scalar_one_or_none()

        if existing is None:
            user = User(
                email=DEV_EMAIL,
                username=DEV_USERNAME,
                hashed_password=hash_password(DEV_PASSWORD),
                role=UserRole.COMPETITIVE,
                is_active=True,
                is_verified=True,
            )
            session.add(user)
            action = "created"
        else:
            existing.email = DEV_EMAIL  # repair a possibly-invalid prior email
            existing.hashed_password = hash_password(DEV_PASSWORD)
            existing.is_active = True
            existing.is_verified = True
            user = existing
            action = "updated"

        await session.commit()
        user_id = str(user.id)

    print(f"dev user {action}: id={user_id}")
    print(f"  login email    : {DEV_EMAIL}")
    print(f"  login password : {DEV_PASSWORD}")
    print(f"  access token   : {create_access_token(user_id)}")


if __name__ == "__main__":
    asyncio.run(main())

"""Per-user API cost budget enforcement."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_usage import ApiUsage

logger = logging.getLogger(__name__)

TIER_TOKEN_BUDGETS = {
    "free": 50_000,
    "competitive": 500_000,
    "elite": 2_000_000,
    "team": 10_000_000,
}


async def check_budget(db: AsyncSession, user_id: str, tier: str) -> bool:
    """Return True if the user still has budget remaining this month."""
    budget = TIER_TOKEN_BUDGETS.get(tier.lower(), 50_000)
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(
            func.coalesce(
                func.sum(ApiUsage.input_tokens + ApiUsage.output_tokens), 0
            )
        ).where(ApiUsage.user_id == user_id, ApiUsage.created_at >= month_start)
    )
    total = result.scalar_one()
    return total < budget


async def log_usage(
    db: AsyncSession,
    user_id: str,
    agent: str,
    input_tokens: int,
    output_tokens: int,
    title_id: str = "",
    cached: bool = False,
) -> None:
    """Record a single API call's token usage and estimated cost."""
    cost = (input_tokens * 0.000003) + (output_tokens * 0.000015)
    usage = ApiUsage(
        user_id=user_id,
        agent=agent,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=cost,
        title_id=title_id,
        cached=cached,
    )
    db.add(usage)
    await db.commit()

"""Usage endpoints — current-month budget and historical daily breakdown."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.api_usage import ApiUsage
from app.models.user import User
from app.services.ai.cost_guard import TIER_TOKEN_BUDGETS

router = APIRouter(tags=["Usage"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class UsageSummary(BaseModel):
    total_tokens: int
    total_cost: float
    budget_tokens: int
    percentage_used: float


class DailyUsage(BaseModel):
    date: str
    tokens: int
    cost: float


class UsageHistoryResponse(BaseModel):
    days: list[DailyUsage]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/current", response_model=UsageSummary)
async def get_current_usage(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageSummary:
    """Return current month's usage for the authenticated user."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(
            func.coalesce(
                func.sum(ApiUsage.input_tokens + ApiUsage.output_tokens), 0
            ),
            func.coalesce(func.sum(ApiUsage.cost), 0.0),
        ).where(
            ApiUsage.user_id == str(user.id),
            ApiUsage.created_at >= month_start,
        )
    )
    row = result.one()
    total_tokens = int(row[0])
    total_cost = float(row[1])

    tier = getattr(user, "tier", None) or getattr(user, "role", "free")
    budget = TIER_TOKEN_BUDGETS.get(str(tier).lower(), 50_000)
    pct = round((total_tokens / budget) * 100, 2) if budget > 0 else 100.0

    return UsageSummary(
        total_tokens=total_tokens,
        total_cost=round(total_cost, 6),
        budget_tokens=budget,
        percentage_used=pct,
    )


@router.get("/history", response_model=UsageHistoryResponse)
async def get_usage_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageHistoryResponse:
    """Return daily usage breakdown for the last 30 days."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)

    result = await db.execute(
        select(
            cast(ApiUsage.created_at, Date).label("day"),
            func.sum(ApiUsage.input_tokens + ApiUsage.output_tokens).label("tokens"),
            func.sum(ApiUsage.cost).label("cost"),
        )
        .where(
            ApiUsage.user_id == str(user.id),
            ApiUsage.created_at >= cutoff,
        )
        .group_by(cast(ApiUsage.created_at, Date))
        .order_by(cast(ApiUsage.created_at, Date))
    )

    days = [
        DailyUsage(date=str(row.day), tokens=int(row.tokens), cost=round(float(row.cost), 6))
        for row in result.all()
    ]
    return UsageHistoryResponse(days=days)

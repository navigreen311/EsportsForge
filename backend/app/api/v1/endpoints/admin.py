"""Admin dashboard endpoints — overview metrics, user management, AI stats."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.user import User, UserRole

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_admin(user: User) -> None:
    """Raise 403 if the user is not an admin (TEAM tier used as proxy)."""
    if user.role != UserRole.TEAM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )


# ---------------------------------------------------------------------------
# GET /admin/overview
# ---------------------------------------------------------------------------

@router.get("/overview")
async def admin_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return high-level platform metrics (mock for now)."""
    _require_admin(current_user)

    # Real user count from DB
    total_result = await db.execute(select(func.count()).select_from(User))
    total_users = total_result.scalar() or 0

    return {
        "total_users": total_users,
        "dau": 3_219,
        "mrr": 87_420,
        "churn_rate": 2.1,
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "claude_api": "healthy",
            "voiceforge": "degraded",
            "visionaudioforge": "healthy",
        },
    }


# ---------------------------------------------------------------------------
# GET /admin/users
# ---------------------------------------------------------------------------

@router.get("/users")
async def admin_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tier: str | None = Query(None),
    search: str | None = Query(None),
):
    """Return paginated user list from the database."""
    _require_admin(current_user)

    query = select(User)

    if tier:
        query = query.where(User.role == tier)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            (User.email.ilike(pattern)) | (User.username.ilike(pattern))
        )

    # Total count
    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Paginated results
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "username": u.username,
                "tier": u.tier,
                "active_title": u.active_title,
                "is_active": u.is_active,
                "created_at": str(u.created_at) if u.created_at else None,
                "updated_at": str(u.updated_at) if u.updated_at else None,
            }
            for u in users
        ],
    }


# ---------------------------------------------------------------------------
# GET /admin/ai-stats
# ---------------------------------------------------------------------------

@router.get("/ai-stats")
async def admin_ai_stats(
    current_user: User = Depends(get_current_user),
):
    """Return AI usage statistics (mock data)."""
    _require_admin(current_user)

    return {
        "tokens_today": 1_240_000,
        "tokens_month": 28_600_000,
        "cost_today_usd": 18.60,
        "cost_month_usd": 429.00,
        "calls_today": 3_842,
        "calls_month": 87_210,
        "cache_hit_rate": 72.4,
        "agents": [
            {"name": "ForgeCore",     "calls": 12_400, "accuracy": 94.2},
            {"name": "LoopAI",        "calls": 9_800,  "accuracy": 91.8},
            {"name": "TruthEngine",   "calls": 8_100,  "accuracy": 96.1},
            {"name": "ImpactRank",    "calls": 6_700,  "accuracy": 89.5},
            {"name": "TransferAI",    "calls": 5_200,  "accuracy": 87.3},
            {"name": "BenchmarkAI",   "calls": 4_900,  "accuracy": 92.0},
            {"name": "CalibrationAI", "calls": 3_100,  "accuracy": 90.7},
        ],
    }

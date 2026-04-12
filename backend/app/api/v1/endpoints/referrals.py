"""Referral system endpoints."""

from __future__ import annotations

import random
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.referral import Referral
from app.models.user import User

router = APIRouter(tags=["Referrals"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ReferralCodeResponse(BaseModel):
    code: str
    share_url: str


class ReferralStatsResponse(BaseModel):
    total_referred: int
    total_converted: int
    months_earned: int


class TrackReferralRequest(BaseModel):
    referral_code: str


class TrackReferralResponse(BaseModel):
    status: str
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_code(username: str) -> str:
    """Generate referral code in format: {username}-{6random}."""
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{username}-{suffix}"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/code", response_model=ReferralCodeResponse)
async def get_or_create_referral_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get or generate a referral code for the current user."""
    result = await db.execute(
        select(Referral)
        .where(Referral.referrer_id == str(current_user.id))
        .where(Referral.status == "pending")
        .where(Referral.referred_id.is_(None))
        .limit(1)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return ReferralCodeResponse(
            code=existing.code,
            share_url=f"https://esportsforge.com/join?ref={existing.code}",
        )

    code = _generate_code(current_user.username if hasattr(current_user, "username") else "user")
    referral = Referral(
        referrer_id=str(current_user.id),
        code=code,
        status="pending",
    )
    db.add(referral)
    await db.flush()

    return ReferralCodeResponse(
        code=code,
        share_url=f"https://esportsforge.com/join?ref={code}",
    )


@router.get("/stats", response_model=ReferralStatsResponse)
async def get_referral_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return referral statistics for the current user."""
    total_result = await db.execute(
        select(func.count())
        .select_from(Referral)
        .where(Referral.referrer_id == str(current_user.id))
        .where(Referral.referred_id.isnot(None))
    )
    total_referred = total_result.scalar() or 0

    converted_result = await db.execute(
        select(func.count())
        .select_from(Referral)
        .where(Referral.referrer_id == str(current_user.id))
        .where(Referral.status.in_(["converted", "rewarded"]))
    )
    total_converted = converted_result.scalar() or 0

    rewarded_result = await db.execute(
        select(func.count())
        .select_from(Referral)
        .where(Referral.referrer_id == str(current_user.id))
        .where(Referral.status == "rewarded")
    )
    months_earned = rewarded_result.scalar() or 0

    return ReferralStatsResponse(
        total_referred=total_referred,
        total_converted=total_converted,
        months_earned=months_earned,
    )


@router.post("/track", response_model=TrackReferralResponse)
async def track_referral(
    body: TrackReferralRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Track a referral signup — links the referral code to the new user."""
    result = await db.execute(
        select(Referral).where(Referral.code == body.referral_code)
    )
    referral = result.scalar_one_or_none()

    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid referral code.",
        )

    if referral.referred_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Referral code already used.",
        )

    if referral.referrer_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot use your own referral code.",
        )

    referral.referred_id = str(current_user.id)
    referral.status = "converted"
    referral.converted_at = datetime.now(timezone.utc)
    await db.flush()

    return TrackReferralResponse(
        status="converted",
        message="Referral tracked successfully.",
    )

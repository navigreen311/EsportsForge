"""Push notification subscription endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.push_subscription import PushSubscription
from app.models.user import User

router = APIRouter(tags=["Push"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SubscribeRequest(BaseModel):
    subscription_json: str  # PushSubscription JSON string from browser


class SubscribeResponse(BaseModel):
    status: str
    message: str


class PushStatusResponse(BaseModel):
    subscribed: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/subscribe", response_model=SubscribeResponse)
async def subscribe(
    body: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Store a push subscription for the authenticated user."""
    # Remove any existing subscription for this user first
    await db.execute(
        delete(PushSubscription).where(
            PushSubscription.user_id == str(current_user.id)
        )
    )

    sub = PushSubscription(
        user_id=str(current_user.id),
        subscription_json=body.subscription_json,
    )
    db.add(sub)
    await db.flush()

    return SubscribeResponse(status="subscribed", message="Push subscription stored.")


@router.delete("/unsubscribe", response_model=SubscribeResponse)
async def unsubscribe(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove push subscription for the authenticated user."""
    result = await db.execute(
        delete(PushSubscription).where(
            PushSubscription.user_id == str(current_user.id)
        )
    )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found.",
        )

    return SubscribeResponse(status="unsubscribed", message="Push subscription removed.")


@router.get("/status", response_model=PushStatusResponse)
async def push_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if the user has an active push subscription."""
    result = await db.execute(
        select(PushSubscription.id)
        .where(PushSubscription.user_id == str(current_user.id))
        .limit(1)
    )
    exists = result.scalar_one_or_none() is not None

    return PushStatusResponse(subscribed=exists)

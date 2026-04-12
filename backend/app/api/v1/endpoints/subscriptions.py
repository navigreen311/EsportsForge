"""Stripe subscription management endpoints."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Tier -> Stripe Price ID mapping
# ---------------------------------------------------------------------------

TIER_FEATURES: dict[str, list[str]] = {
    "free": ["1 game title", "Basic analytics", "Community access"],
    "competitive": [
        "3 game titles",
        "Advanced analytics",
        "AI coaching",
        "Priority support",
    ],
    "elite": [
        "6 game titles",
        "Full analytics suite",
        "AI coaching + game plans",
        "Film review",
        "Priority support",
    ],
    "team": [
        "Unlimited game titles",
        "Full analytics suite",
        "AI coaching + game plans",
        "Film review",
        "Team management",
        "Dedicated support",
    ],
}


def _price_id_for_tier(tier: str) -> str | None:
    """Return the Stripe Price ID for a given tier name."""
    mapping = {
        "competitive": settings.stripe_price_competitive,
        "elite": settings.stripe_price_elite,
        "team": settings.stripe_price_team,
    }
    return mapping.get(tier.lower())


def _stripe_available() -> bool:
    """Return True when Stripe keys are configured."""
    return bool(settings.stripe_secret_key)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class CheckoutRequest(BaseModel):
    tier: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class SubscriptionInfo(BaseModel):
    tier: str
    is_active: bool
    features: list[str]


class CancelResponse(BaseModel):
    status: str


class Invoice(BaseModel):
    id: str
    date: str
    amount: str
    status: str


# ---------------------------------------------------------------------------
# POST /checkout
# ---------------------------------------------------------------------------


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a Stripe Checkout session for upgrading the subscription."""
    tier = body.tier.lower()

    if tier not in ("competitive", "elite", "team"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {body.tier}. Must be competitive, elite, or team.",
        )

    price_id = _price_id_for_tier(tier)

    # If Stripe is not configured, return a mock response
    if not _stripe_available() or not price_id:
        mock_session_id = f"mock_sess_{uuid.uuid4().hex[:16]}"
        return CheckoutResponse(
            checkout_url=f"https://checkout.stripe.com/mock/{mock_session_id}",
            session_id=mock_session_id,
        )

    try:
        import stripe

        stripe.api_key = settings.stripe_secret_key

        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url="http://localhost:3000/settings?session_id={CHECKOUT_SESSION_ID}&status=success",
            cancel_url="http://localhost:3000/settings?status=cancelled",
            client_reference_id=str(current_user.id),
            customer_email=current_user.email,
            metadata={"user_id": str(current_user.id), "tier": tier},
        )

        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.id,
        )
    except Exception as exc:
        logger.error("Stripe checkout error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment service unavailable. Please try again later.",
        )


# ---------------------------------------------------------------------------
# POST /webhook
# ---------------------------------------------------------------------------


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request):
    """Handle incoming Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not _stripe_available():
        logger.warning("Stripe webhook received but Stripe is not configured.")
        return {"status": "ignored"}

    try:
        import stripe

        stripe.api_key = settings.stripe_secret_key

        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as exc:
        logger.error("Webhook signature verification failed: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id = data_object.get("client_reference_id") or data_object.get(
            "metadata", {}
        ).get("user_id")
        tier = data_object.get("metadata", {}).get("tier", "competitive")
        logger.info(
            "Checkout completed for user %s — upgrading to %s", user_id, tier
        )
        # In production: update user.role in the DB here.

    elif event_type == "customer.subscription.deleted":
        logger.info("Subscription deleted: %s", data_object.get("id"))
        # In production: downgrade user to FREE tier here.

    elif event_type == "invoice.payment_failed":
        logger.warning(
            "Payment failed for subscription %s",
            data_object.get("subscription"),
        )
        # In production: notify the user and/or apply grace period.

    else:
        logger.debug("Unhandled webhook event type: %s", event_type)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /current
# ---------------------------------------------------------------------------


@router.get("/current", response_model=SubscriptionInfo)
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
):
    """Return the current user's subscription tier and feature set."""
    tier = current_user.tier  # property returns role.value (str)
    return SubscriptionInfo(
        tier=tier,
        is_active=current_user.is_active,
        features=TIER_FEATURES.get(tier, TIER_FEATURES["free"]),
    )


# ---------------------------------------------------------------------------
# POST /cancel
# ---------------------------------------------------------------------------


@router.post("/cancel", response_model=CancelResponse)
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
):
    """Schedule cancellation of the current subscription at period end."""
    if current_user.role == UserRole.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active paid subscription to cancel.",
        )

    # In production: call stripe.Subscription.modify(cancel_at_period_end=True)
    logger.info(
        "Cancellation scheduled for user %s (tier: %s)",
        current_user.id,
        current_user.tier,
    )
    return CancelResponse(status="cancellation_scheduled")


# ---------------------------------------------------------------------------
# GET /invoices
# ---------------------------------------------------------------------------


@router.get("/invoices", response_model=list[Invoice])
async def list_invoices(
    current_user: User = Depends(get_current_user),
):
    """Return recent invoices for the current user (mock data)."""
    now = datetime.now(timezone.utc)
    mock_invoices = [
        Invoice(
            id=f"inv_{uuid.uuid4().hex[:12]}",
            date=(now.replace(month=max(now.month - i, 1))).strftime("%Y-%m-%d"),
            amount="$19.99" if current_user.role == UserRole.COMPETITIVE
            else "$49.99" if current_user.role == UserRole.ELITE
            else "$149.99" if current_user.role == UserRole.TEAM
            else "$0.00",
            status="paid",
        )
        for i in range(3)
    ]
    return mock_invoices

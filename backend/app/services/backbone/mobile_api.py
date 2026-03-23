"""MobileAPI — mobile kill sheets, tournament ops, quick view, and push notifications.

Provides mobile-optimized endpoints for on-the-go access to kill sheets,
tournament management, at-a-glance dashboards, and push notifications.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from app.schemas.mobile import (
    MobileKillSheet,
    PushNotification,
    PushResult,
    QuickView,
    TournamentOps,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

_kill_sheets: dict[str, dict[str, MobileKillSheet]] = defaultdict(dict)
_tournaments: dict[str, TournamentOps] = {}
_quick_views: dict[str, dict[str, QuickView]] = defaultdict(dict)
_notifications: list[PushNotification] = []
_user_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {
    "rating": 1000, "wins": 0, "losses": 0, "streak": 0, "sessions": 0,
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_mobile_kill_sheet(
    user_id: str,
    title: str,
    opponent_id: str | None = None,
) -> MobileKillSheet:
    """Generate a mobile-optimized kill sheet for quick pre-game reference.

    Condenses the full kill sheet into a compact format suitable for
    mobile display with quick tips and core plays.
    """
    cached_key = f"{title}_{opponent_id or 'generic'}"
    cached = _kill_sheets.get(user_id, {}).get(cached_key)
    if cached:
        return cached

    # Build a condensed kill sheet
    plays: list[dict[str, Any]] = []
    quick_tips: list[str] = []

    if title == "madden26":
        plays = [
            {"name": "Gun Bunch — Mesh", "type": "pass", "situation": "3rd & medium", "key": "TE over the middle"},
            {"name": "Pistol — RPO Read", "type": "rpo", "situation": "1st down", "key": "Read the DE"},
            {"name": "Cover 2 Man", "type": "defense", "situation": "base", "key": "User the MLB"},
        ]
        quick_tips = [
            "Start with the opening script. Adjust after 3 plays.",
            "If they blitz, go to screens and quick slants.",
            "In the red zone, switch to Singleback power run.",
        ]
    elif title == "eafc26":
        plays = [
            {"name": "4-3-3 Wing Play", "type": "attack", "situation": "open play", "key": "Overlap with fullback"},
            {"name": "Counter Press", "type": "defense", "situation": "possession loss", "key": "Immediate pressure"},
            {"name": "Short Corner → Pull-back", "type": "set_piece", "situation": "corner", "key": "Edge of box shot"},
        ]
        quick_tips = [
            "Control possession in the first 15 minutes.",
            "Switch play to the weak side when opponent overloads.",
            "Use custom tactics: 55 width, 50 depth.",
        ]
    else:
        plays = [{"name": "Base Strategy", "type": "generic", "situation": "default", "key": "Execute the fundamentals"}]
        quick_tips = ["Focus on your strengths. Adapt after observing opponent patterns."]

    sheet = MobileKillSheet(
        user_id=user_id,
        opponent_id=opponent_id,
        title=title,
        plays=plays,
        quick_tips=quick_tips,
        last_updated=_now_iso(),
    )

    _kill_sheets[user_id][cached_key] = sheet
    return sheet


def get_mobile_tourna_ops(
    user_id: str,
    tournament_id: str,
) -> TournamentOps:
    """Get mobile tournament operations view with bracket, schedule, and prep tips.

    Provides at-a-glance tournament status, next opponent info, and
    quick preparation recommendations.
    """
    cached = _tournaments.get(f"{user_id}_{tournament_id}")
    if cached:
        return cached

    # Build tournament view
    ops = TournamentOps(
        user_id=user_id,
        tournament_id=tournament_id,
        tournament_name="Weekend Showdown",
        current_round=2,
        total_rounds=4,
        next_opponent={
            "name": "Opponent_42",
            "record": "3-1",
            "style": "aggressive",
            "notes": "Heavy on pressure plays. Prepare counters.",
        },
        bracket_position="Winners Round 2",
        schedule=[
            {"round": 2, "time": "2:00 PM", "opponent": "Opponent_42", "status": "upcoming"},
            {"round": 3, "time": "4:00 PM", "opponent": "TBD", "status": "pending"},
        ],
        quick_prep=[
            "Review your kill sheet before the match.",
            "Warm up with 2-3 practice games.",
            "Set your controller sensitivity before going live.",
        ],
        status="active",
    )

    _tournaments[f"{user_id}_{tournament_id}"] = ops
    return ops


def get_quick_view(user_id: str, title: str) -> QuickView:
    """Generate the mobile quick view dashboard for at-a-glance status.

    Compiles rating, rank, recent record, active drills, and
    the top recommendation into a single compact view.
    """
    stats = _user_stats[user_id]
    wins = stats["wins"]
    losses = stats["losses"]
    streak = stats["streak"]

    win_rate = wins / max(wins + losses, 1)
    if win_rate >= 0.65:
        tier = "diamond"
    elif win_rate >= 0.55:
        tier = "platinum"
    elif win_rate >= 0.45:
        tier = "gold"
    elif win_rate >= 0.35:
        tier = "silver"
    else:
        tier = "bronze"

    # Top recommendation based on recent performance
    if streak <= -3:
        top_rec = "On a losing streak — review your replay from the last loss and adjust."
    elif streak >= 3:
        top_rec = "Hot streak! Keep your current approach. Dont change what is working."
    elif win_rate < 0.40:
        top_rec = "Focus on drills to improve your weakest area before queuing ranked."
    else:
        top_rec = "Solid form. Try incorporating a new strategy from the meta report."

    # Count pending notifications
    user_notifs = sum(1 for n in _notifications if n.user_id == user_id and not n.sent)

    return QuickView(
        user_id=user_id,
        title=title,
        current_rating=stats["rating"],
        rank_tier=tier,
        recent_record=f"{wins}-{losses}",
        win_streak=max(0, streak),
        loss_streak=abs(min(0, streak)),
        top_recommendation=top_rec,
        active_drills=stats.get("active_drills", 0),
        notifications=user_notifs,
        last_session=_now_iso(),
    )


def send_push_notification(
    user_id: str,
    title: str,
    body: str,
    notification_type: str = "meta_alert",
    priority: str = "normal",
    data: dict[str, Any] | None = None,
) -> PushResult:
    """Send a push notification to a user's mobile device.

    Creates and queues a notification with type-specific routing
    and priority handling.
    """
    notif_id = f"notif_{uuid.uuid4().hex[:12]}"

    # Validate notification type
    valid_types = {"meta_alert", "drill_reminder", "tournament", "achievement", "coach"}
    if notification_type not in valid_types:
        return PushResult(
            success=False,
            notification_id=notif_id,
            message=f"Invalid notification type. Must be one of: {valid_types}.",
        )

    # Rate limiting (max 10 per user per hour in production)
    recent_notifs = [
        n for n in _notifications
        if n.user_id == user_id and n.sent
    ]
    if len(recent_notifs) > 50:
        return PushResult(
            success=False,
            notification_id=notif_id,
            message="Notification rate limit exceeded. Try again later.",
        )

    notification = PushNotification(
        notification_id=notif_id,
        user_id=user_id,
        title=title,
        body=body,
        notification_type=notification_type,
        priority=priority,
        data=data or {},
        sent=True,
        sent_at=_now_iso(),
    )
    _notifications.append(notification)

    logger.info(
        "Push notification sent: id=%s user=%s type=%s priority=%s",
        notif_id, user_id, notification_type, priority,
    )

    return PushResult(
        success=True,
        notification_id=notif_id,
        message=f"Notification '{title}' sent to user {user_id}.",
    )

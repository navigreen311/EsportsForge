"""AnimaForge push-notification hook.

The webhook handler calls :func:`send_animaforge_push` whenever a render
completes for a real (non-``"system"``) user. Today this is a stub: the
existing push-subscription infrastructure (``app/models/push_subscription.py``,
``app/api/v1/endpoints/push.py``) only stores Web-Push subscriptions — there
is no server-side dispatch service yet (no ``pywebpush`` integration, no
VAPID keys, no broker). When that infra lands, swap the TODO body below
for the real send.

Keeping the function as a no-op-with-logging means the webhook can call it
unconditionally without ImportError or runtime failure today.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def send_animaforge_push(
    user_id: str,
    title: str,
    body: str,
    action_url: str,
) -> None:
    """Send a push notification to ``user_id`` for a completed AnimaForge job.

    Args:
        user_id: Target user (``"system"`` is filtered out by the webhook
            before it reaches this function).
        title: Notification title (e.g. ``"Animation Ready"``).
        body: Notification body copy.
        action_url: Where to send the user when they tap the notification.

    TODO(animaforge-push): wire into the eventual web-push dispatcher.
    The push subscription rows already exist in ``push_subscriptions`` —
    look them up by ``user_id`` and dispatch via ``pywebpush`` once VAPID
    keys are configured. Until then this stub logs the notification so
    the webhook flow is observable end-to-end in dev.
    """
    logger.info(
        "animaforge.push_stub user_id=%s title=%r body=%r action_url=%s",
        user_id,
        title,
        body,
        action_url,
    )

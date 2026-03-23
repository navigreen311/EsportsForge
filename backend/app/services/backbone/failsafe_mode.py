"""FailSafe Mode — offline cached fallback for tournament-day reliability.

When connectivity drops or the user manually activates failsafe, the system
switches to pre-cached gameplans and a simplified UI that guarantees
zero-latency access to critical intel.
"""

from __future__ import annotations

from datetime import datetime

from app.services.backbone.trust_layer import TrustLayer


# ---------------------------------------------------------------------------
# In-memory stores (replaced by persistent cache in production)
# ---------------------------------------------------------------------------
_failsafe_active: dict[str, bool] = {}
_cached_gameplans: dict[str, dict[str, dict]] = {}  # user_id -> {title: gameplan}


# ---------------------------------------------------------------------------
# FailSafe Mode service
# ---------------------------------------------------------------------------

class FailSafeMode:
    """Offline cached mode for tournament-day resilience."""

    @staticmethod
    def activate_failsafe(user_id: str) -> dict:
        """Switch *user_id* to offline cached mode.

        Returns confirmation with the activation timestamp.
        """
        _failsafe_active[user_id] = True
        TrustLayer.audit_log(
            "failsafe_activated",
            user_id,
            "User switched to offline failsafe mode.",
        )
        return {
            "user_id": user_id,
            "failsafe_active": True,
            "activated_at": datetime.utcnow().isoformat(),
            "message": "FailSafe mode active. Using cached gameplans and simplified UI.",
        }

    @staticmethod
    def deactivate_failsafe(user_id: str) -> dict:
        """Return *user_id* to normal online mode."""
        _failsafe_active[user_id] = False
        TrustLayer.audit_log(
            "failsafe_deactivated",
            user_id,
            "User returned to online mode.",
        )
        return {
            "user_id": user_id,
            "failsafe_active": False,
            "deactivated_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def is_active(user_id: str) -> bool:
        """Return whether failsafe mode is active for *user_id*."""
        return _failsafe_active.get(user_id, False)

    @staticmethod
    def cache_gameplan(user_id: str, title: str, gameplan: dict) -> None:
        """Store a gameplan in the offline cache for later retrieval."""
        _cached_gameplans.setdefault(user_id, {})[title] = gameplan
        TrustLayer.audit_log(
            "gameplan_cached",
            user_id,
            f"Gameplan '{title}' cached for offline use.",
        )

    @staticmethod
    def get_cached_gameplan(user_id: str, title: str) -> dict | None:
        """Retrieve a cached gameplan by *title* for *user_id*.

        Returns ``None`` if no cached plan exists.
        """
        return _cached_gameplans.get(user_id, {}).get(title)

    @staticmethod
    def get_simplified_ui_config() -> dict:
        """Return the tournament-day simplified UI configuration.

        This is a static config that strips down the UI to essentials:
        gameplan viewer, play-call sheet, and timeout notes.
        """
        return {
            "theme": "tournament_minimal",
            "panels_visible": [
                "gameplan_viewer",
                "play_call_sheet",
                "timeout_notes",
            ],
            "panels_hidden": [
                "tendency_charts",
                "film_room",
                "roster_deep_dive",
                "loop_ai_suggestions",
                "social_feed",
            ],
            "animations_enabled": False,
            "auto_refresh_enabled": False,
            "offline_indicator": True,
            "font_size": "large",
            "high_contrast": True,
        }

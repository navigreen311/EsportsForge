"""Trust Layer — privacy governance, data permissions, and audit compliance.

Manages user opt-in/out controls, data access authorization, GDPR-style
deletion and export, and a full audit trail of every data operation.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from app.schemas.integrity import (
    AuditEvent,
    DataPermission,
    PrivacySettings,
)


# ---------------------------------------------------------------------------
# In-memory stores (replaced by DB in production)
# ---------------------------------------------------------------------------
_privacy_store: dict[str, PrivacySettings] = {}
_audit_store: dict[str, list[AuditEvent]] = {}


# ---------------------------------------------------------------------------
# Trust Layer service
# ---------------------------------------------------------------------------

class TrustLayer:
    """Privacy and data governance for EsportsForge."""

    # -- Privacy settings ---------------------------------------------------

    @staticmethod
    def get_privacy_settings(user_id: str) -> PrivacySettings:
        """Return the current privacy settings for *user_id*.

        Creates a default (all-opt-out) profile when none exists.
        """
        if user_id in _privacy_store:
            return _privacy_store[user_id]

        default = PrivacySettings(
            user_id=user_id,
            permissions={p: False for p in DataPermission},
        )
        _privacy_store[user_id] = default
        TrustLayer.audit_log("privacy_defaults_created", user_id, "Default privacy profile created (all opted out).")
        return default

    @staticmethod
    def update_privacy(
        user_id: str,
        permissions: dict[DataPermission, bool],
    ) -> PrivacySettings:
        """Merge *permissions* into the user's existing privacy profile."""
        current = TrustLayer.get_privacy_settings(user_id)
        current.permissions.update(permissions)
        current.updated_at = datetime.utcnow()
        if current.opted_in_at is None and any(permissions.values()):
            current.opted_in_at = datetime.utcnow()
        _privacy_store[user_id] = current

        changed = ", ".join(f"{k.value}={v}" for k, v in permissions.items())
        TrustLayer.audit_log("privacy_updated", user_id, f"Permissions changed: {changed}")
        return current

    # -- Data access checks -------------------------------------------------

    @staticmethod
    def check_data_access(
        user_id: str,
        requester: str,
        data_type: DataPermission,
    ) -> bool:
        """Return ``True`` if *requester* may access *data_type* for *user_id*.

        Self-access is always permitted.  Third-party access requires an
        explicit opt-in for the corresponding ``DataPermission``.
        """
        if requester == user_id:
            TrustLayer.audit_log(
                "data_access_self",
                user_id,
                f"Self-access to {data_type.value} granted.",
            )
            return True

        settings = TrustLayer.get_privacy_settings(user_id)
        allowed = settings.permissions.get(data_type, False)

        TrustLayer.audit_log(
            "data_access_check",
            user_id,
            f"Requester={requester}, data_type={data_type.value}, allowed={allowed}",
        )
        return allowed

    # -- Audit trail --------------------------------------------------------

    @staticmethod
    def audit_log(action: str, user_id: str, details: str = "") -> AuditEvent:
        """Record an audit event and return it."""
        event = AuditEvent(
            event_id=uuid.uuid4().hex,
            action=action,
            user_id=user_id,
            details=details,
            timestamp=datetime.utcnow(),
        )
        _audit_store.setdefault(user_id, []).append(event)
        return event

    @staticmethod
    def get_audit_trail(user_id: str) -> list[AuditEvent]:
        """Return the full audit trail for *user_id*."""
        return list(_audit_store.get(user_id, []))

    # -- GDPR-style data operations -----------------------------------------

    @staticmethod
    def handle_data_deletion(user_id: str) -> dict:
        """Delete all stored data for *user_id* (GDPR right-to-erasure).

        Returns a summary of what was removed.
        """
        # Record the deletion itself before wiping the trail
        TrustLayer.audit_log("data_deletion_requested", user_id, "User requested full data deletion.")

        deleted: dict[str, bool] = {}

        # Privacy settings
        deleted["privacy_settings"] = user_id in _privacy_store
        _privacy_store.pop(user_id, None)

        # Audit trail — keep a tombstone record for legal compliance
        audit_count = len(_audit_store.get(user_id, []))
        deleted["audit_events"] = audit_count > 0
        deleted["audit_events_count"] = audit_count  # type: ignore[assignment]

        # Replace with a single tombstone
        _audit_store[user_id] = [
            AuditEvent(
                event_id=uuid.uuid4().hex,
                action="data_deleted",
                user_id=user_id,
                details=f"All user data deleted. {audit_count} audit events removed.",
                timestamp=datetime.utcnow(),
            )
        ]

        return deleted

    @staticmethod
    def export_user_data(user_id: str) -> dict:
        """Export all data held for *user_id* (GDPR right-to-portability).

        Returns a dictionary suitable for JSON serialization.
        """
        TrustLayer.audit_log("data_export_requested", user_id, "User requested data export.")

        privacy = TrustLayer.get_privacy_settings(user_id)
        audit_trail = TrustLayer.get_audit_trail(user_id)

        return {
            "user_id": user_id,
            "exported_at": datetime.utcnow().isoformat(),
            "privacy_settings": privacy.model_dump(mode="json"),
            "audit_trail": [e.model_dump(mode="json") for e in audit_trail],
        }

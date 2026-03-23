"""Unit tests for the Trust Layer — privacy, audit, data export/deletion."""

import pytest

from app.schemas.integrity import (
    AuditEvent,
    DataPermission,
    PrivacySettings,
)
from app.services.backbone.trust_layer import (
    TrustLayer,
    _audit_store,
    _privacy_store,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_state():
    """Reset in-memory stores between tests."""
    _privacy_store.clear()
    _audit_store.clear()
    yield
    _privacy_store.clear()
    _audit_store.clear()


# ---------------------------------------------------------------------------
# Privacy settings
# ---------------------------------------------------------------------------

class TestPrivacySettings:
    """Tests for get_privacy_settings / update_privacy."""

    def test_default_all_opted_out(self):
        settings = TrustLayer.get_privacy_settings("user-1")
        assert settings.user_id == "user-1"
        assert all(v is False for v in settings.permissions.values())

    def test_update_privacy_merges(self):
        TrustLayer.get_privacy_settings("user-1")
        updated = TrustLayer.update_privacy("user-1", {DataPermission.SHARE_STATS: True})
        assert updated.permissions[DataPermission.SHARE_STATS] is True
        # Others remain False
        assert updated.permissions[DataPermission.SHARE_REPLAYS] is False

    def test_update_sets_opted_in_at(self):
        TrustLayer.get_privacy_settings("user-1")
        updated = TrustLayer.update_privacy("user-1", {DataPermission.ALLOW_ANALYTICS: True})
        assert updated.opted_in_at is not None

    def test_update_does_not_reset_opted_in_at_on_all_false(self):
        TrustLayer.update_privacy("user-1", {DataPermission.SHARE_STATS: True})
        first_opted = TrustLayer.get_privacy_settings("user-1").opted_in_at
        TrustLayer.update_privacy("user-1", {DataPermission.SHARE_STATS: False})
        assert TrustLayer.get_privacy_settings("user-1").opted_in_at == first_opted


# ---------------------------------------------------------------------------
# Data access checks
# ---------------------------------------------------------------------------

class TestDataAccess:
    """Tests for check_data_access."""

    def test_self_access_always_allowed(self):
        assert TrustLayer.check_data_access("user-1", "user-1", DataPermission.SHARE_STATS) is True

    def test_third_party_denied_by_default(self):
        TrustLayer.get_privacy_settings("user-1")
        assert TrustLayer.check_data_access("user-1", "opponent-1", DataPermission.SHARE_STATS) is False

    def test_third_party_allowed_after_opt_in(self):
        TrustLayer.update_privacy("user-1", {DataPermission.SHARE_STATS: True})
        assert TrustLayer.check_data_access("user-1", "opponent-1", DataPermission.SHARE_STATS) is True

    def test_third_party_denied_for_non_opted_type(self):
        TrustLayer.update_privacy("user-1", {DataPermission.SHARE_STATS: True})
        assert TrustLayer.check_data_access("user-1", "opponent-1", DataPermission.SHARE_REPLAYS) is False


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------

class TestAuditTrail:
    """Tests for audit_log / get_audit_trail."""

    def test_audit_log_creates_event(self):
        event = TrustLayer.audit_log("test_action", "user-1", "testing")
        assert isinstance(event, AuditEvent)
        assert event.action == "test_action"
        assert event.user_id == "user-1"

    def test_audit_trail_accumulates(self):
        TrustLayer.audit_log("a1", "user-1")
        TrustLayer.audit_log("a2", "user-1")
        trail = TrustLayer.get_audit_trail("user-1")
        assert len(trail) == 2
        assert trail[0].action == "a1"
        assert trail[1].action == "a2"

    def test_audit_trail_empty_for_unknown_user(self):
        assert TrustLayer.get_audit_trail("nobody") == []

    def test_privacy_operations_generate_audit_events(self):
        TrustLayer.get_privacy_settings("user-1")  # creates default
        TrustLayer.update_privacy("user-1", {DataPermission.SHARE_STATS: True})
        trail = TrustLayer.get_audit_trail("user-1")
        actions = [e.action for e in trail]
        assert "privacy_defaults_created" in actions
        assert "privacy_updated" in actions


# ---------------------------------------------------------------------------
# Data deletion (GDPR)
# ---------------------------------------------------------------------------

class TestDataDeletion:
    """Tests for handle_data_deletion."""

    def test_deletion_removes_privacy_settings(self):
        TrustLayer.update_privacy("user-1", {DataPermission.SHARE_STATS: True})
        TrustLayer.handle_data_deletion("user-1")
        # After deletion, a fresh get should return defaults (all opted out)
        settings = TrustLayer.get_privacy_settings("user-1")
        assert all(v is False for v in settings.permissions.values())

    def test_deletion_leaves_tombstone(self):
        TrustLayer.audit_log("some_action", "user-1")
        TrustLayer.handle_data_deletion("user-1")
        # Only the tombstone plus the new default-create event should remain
        trail = _audit_store.get("user-1", [])
        tombstone = [e for e in trail if e.action == "data_deleted"]
        assert len(tombstone) == 1

    def test_deletion_returns_summary(self):
        TrustLayer.update_privacy("user-1", {DataPermission.SHARE_STATS: True})
        result = TrustLayer.handle_data_deletion("user-1")
        assert "privacy_settings" in result
        assert result["privacy_settings"] is True


# ---------------------------------------------------------------------------
# Data export (GDPR)
# ---------------------------------------------------------------------------

class TestDataExport:
    """Tests for export_user_data."""

    def test_export_contains_required_sections(self):
        TrustLayer.update_privacy("user-1", {DataPermission.SHARE_STATS: True})
        export = TrustLayer.export_user_data("user-1")
        assert export["user_id"] == "user-1"
        assert "exported_at" in export
        assert "privacy_settings" in export
        assert "audit_trail" in export

    def test_export_audit_trail_is_list(self):
        TrustLayer.audit_log("action", "user-1")
        export = TrustLayer.export_user_data("user-1")
        assert isinstance(export["audit_trail"], list)
        assert len(export["audit_trail"]) >= 1

    def test_export_generates_audit_event(self):
        TrustLayer.export_user_data("user-1")
        trail = TrustLayer.get_audit_trail("user-1")
        actions = [e.action for e in trail]
        assert "data_export_requested" in actions

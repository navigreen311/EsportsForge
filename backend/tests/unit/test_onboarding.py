"""Unit tests for Onboarding Intelligence and MetaVersion Engine."""

from __future__ import annotations

import pytest

from app.schemas.film import (
    AdviceStatus,
    FirstGameplan,
    MetaSnapshot,
    MetaVersionStamp,
    OnboardingPhase,
    OnboardingProfile,
    StaleAdviceAlert,
)
from app.services.backbone import meta_version_engine, onboarding_intelligence


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_stores():
    """Reset all in-memory stores before each test."""
    onboarding_intelligence.reset_store()
    meta_version_engine.reset_store()
    yield
    onboarding_intelligence.reset_store()
    meta_version_engine.reset_store()


def _make_session(title: str = "madden26", result: str = "win", plays: list | None = None) -> dict:
    return {
        "title": title,
        "result": result,
        "plays": plays or [],
    }


def _aggressive_session(title: str = "madden26") -> dict:
    return _make_session(
        title=title,
        result="win",
        plays=[
            {"type": "blitz"},
            {"type": "deep_pass"},
            {"type": "aggressive_run"},
            {"type": "blitz"},
        ],
    )


def _conservative_session(title: str = "madden26") -> dict:
    return _make_session(
        title=title,
        result="loss",
        plays=[
            {"type": "short_pass"},
            {"type": "run"},
            {"type": "screen"},
            {"type": "punt"},
        ],
    )


# ===========================================================================
# Onboarding Intelligence
# ===========================================================================

class TestStartOnboarding:
    """Test start_onboarding initializes correctly."""

    def test_creates_profile(self):
        profile = onboarding_intelligence.start_onboarding("user1", "madden26")
        assert isinstance(profile, OnboardingProfile)
        assert profile.user_id == "user1"
        assert profile.title == "madden26"
        assert profile.current_phase == OnboardingPhase.SESSION_1
        assert profile.steps == []

    def test_prevents_double_start_after_completion(self):
        """Cannot restart onboarding once completed."""
        onboarding_intelligence.start_onboarding("user1", "madden26")
        onboarding_intelligence.process_first_session("user1", _make_session())
        onboarding_intelligence.process_second_session("user1", _make_session())
        onboarding_intelligence.process_third_session("user1", _make_session())

        with pytest.raises(ValueError, match="already completed"):
            onboarding_intelligence.start_onboarding("user1", "madden26")


class TestOnboardingFlow:
    """Test the full 3-session onboarding flow."""

    def test_full_flow_completes(self):
        onboarding_intelligence.start_onboarding("user1", "madden26")

        p1 = onboarding_intelligence.process_first_session("user1", _make_session())
        assert p1.current_phase == OnboardingPhase.SESSION_2
        assert len(p1.steps) == 1

        p2 = onboarding_intelligence.process_second_session("user1", _make_session())
        assert p2.current_phase == OnboardingPhase.SESSION_3
        assert len(p2.steps) == 2

        p3 = onboarding_intelligence.process_third_session("user1", _make_session())
        assert p3.current_phase == OnboardingPhase.COMPLETED
        assert len(p3.steps) == 3
        assert p3.completed_at is not None

    def test_out_of_order_raises(self):
        onboarding_intelligence.start_onboarding("user1", "madden26")
        with pytest.raises(ValueError, match="Expected phase SESSION_1"):
            onboarding_intelligence.process_second_session("user1", _make_session())

    def test_no_onboarding_raises(self):
        with pytest.raises(ValueError, match="No onboarding started"):
            onboarding_intelligence.process_first_session("user1", _make_session())

    def test_aggressive_playstyle_detected(self):
        onboarding_intelligence.start_onboarding("user1", "madden26")
        p = onboarding_intelligence.process_first_session("user1", _aggressive_session())
        assert p.preliminary_playstyle == "aggressive"

    def test_conservative_playstyle_detected(self):
        onboarding_intelligence.start_onboarding("user1", "madden26")
        p = onboarding_intelligence.process_first_session("user1", _conservative_session())
        assert p.preliminary_playstyle == "conservative"


class TestFirstGameplan:
    """Test gameplan generation after onboarding."""

    def test_gameplan_after_completion(self):
        onboarding_intelligence.start_onboarding("user1", "madden26")
        onboarding_intelligence.process_first_session("user1", _aggressive_session())
        onboarding_intelligence.process_second_session("user1", _aggressive_session())
        onboarding_intelligence.process_third_session("user1", _aggressive_session())

        gp = onboarding_intelligence.install_first_gameplan("user1", "madden26")
        assert isinstance(gp, FirstGameplan)
        assert gp.user_id == "user1"
        assert gp.recommended_strategy  # non-empty
        assert len(gp.focus_areas) > 0
        assert gp.confidence > 0

    def test_gameplan_before_completion_raises(self):
        onboarding_intelligence.start_onboarding("user1", "madden26")
        with pytest.raises(ValueError, match="not yet completed"):
            onboarding_intelligence.install_first_gameplan("user1", "madden26")


class TestOnboardingProgress:
    """Test progress reporting."""

    def test_empty_progress(self):
        result = onboarding_intelligence.get_onboarding_progress("user1")
        assert result == {}

    def test_progress_during_flow(self):
        onboarding_intelligence.start_onboarding("user1", "madden26")
        onboarding_intelligence.process_first_session("user1", _make_session())

        progress = onboarding_intelligence.get_onboarding_progress("user1")
        assert "madden26" in progress
        assert progress["madden26"]["steps_completed"] == 1
        assert progress["madden26"]["completed"] is False

    def test_progress_filter_by_title(self):
        onboarding_intelligence.start_onboarding("user1", "madden26")
        onboarding_intelligence.start_onboarding("user1", "nba2k26")

        progress = onboarding_intelligence.get_onboarding_progress("user1", title="madden26")
        assert "madden26" in progress
        assert "nba2k26" not in progress


# ===========================================================================
# MetaVersion Engine
# ===========================================================================

class TestCreateSnapshot:
    """Test meta snapshot creation."""

    def test_creates_snapshot(self):
        snap = meta_version_engine.create_snapshot(
            "madden26", "1.04",
            top_strategies=["Gun Trips", "Nickel 335"],
            meta_notes="Post-patch nerf to cover 3",
        )
        assert isinstance(snap, MetaSnapshot)
        assert snap.title == "madden26"
        assert snap.patch_version == "1.04"
        assert "Gun Trips" in snap.top_strategies

    def test_retrieve_snapshot(self):
        meta_version_engine.create_snapshot("madden26", "1.04")
        snap = meta_version_engine.get_snapshot("madden26", "1.04")
        assert snap.patch_version == "1.04"

    def test_missing_snapshot_raises(self):
        with pytest.raises(ValueError, match="No meta snapshot"):
            meta_version_engine.get_snapshot("madden26", "99.0")


class TestStampRecommendation:
    """Test version-stamping recommendations."""

    def test_stamp_creates_record(self):
        stamp = meta_version_engine.stamp_recommendation(
            "Use Gun Trips TE", "1.04", "madden26"
        )
        assert isinstance(stamp, MetaVersionStamp)
        assert stamp.status == AdviceStatus.ACTIVE
        assert stamp.patch_version == "1.04"


class TestStaleAdviceDetection:
    """Test stale advice detection and auto-expiration."""

    def test_detects_stale_advice(self):
        meta_version_engine.stamp_recommendation("Old tip", "1.03", "madden26")
        alerts = meta_version_engine.detect_stale_advice("madden26", "1.04")

        assert len(alerts) == 1
        assert isinstance(alerts[0], StaleAdviceAlert)
        assert alerts[0].stamped_patch == "1.03"
        assert alerts[0].current_patch == "1.04"

    def test_current_patch_not_stale(self):
        meta_version_engine.stamp_recommendation("Fresh tip", "1.04", "madden26")
        alerts = meta_version_engine.detect_stale_advice("madden26", "1.04")
        assert len(alerts) == 0

    def test_auto_expire_marks_old(self):
        meta_version_engine.stamp_recommendation("Tip A", "1.03", "madden26")
        meta_version_engine.stamp_recommendation("Tip B", "1.04", "madden26")

        expired = meta_version_engine.auto_expire_stale("madden26", "1.04")
        assert len(expired) == 1
        assert expired[0].status == AdviceStatus.EXPIRED

    def test_expired_not_re_detected(self):
        meta_version_engine.stamp_recommendation("Old tip", "1.03", "madden26")
        meta_version_engine.auto_expire_stale("madden26", "1.04")
        alerts = meta_version_engine.detect_stale_advice("madden26", "1.05")
        # The 1.03 tip was expired, only 1.04 tip (none here) would show
        assert len(alerts) == 0


class TestPatchChangelog:
    """Test patch changelog retrieval."""

    def test_changelog_between_patches(self):
        meta_version_engine.create_snapshot(
            "madden26", "1.03",
            top_strategies=["Cover 3"],
            changelog_notes=["Initial release"],
        )
        meta_version_engine.create_snapshot(
            "madden26", "1.04",
            top_strategies=["Gun Trips"],
            changelog_notes=["Nerfed Cover 3", "Buffed Gun Trips"],
        )

        changelog = meta_version_engine.get_patch_changelog("madden26", "1.03", "1.04")
        assert changelog["from_patch"] == "1.03"
        assert changelog["to_patch"] == "1.04"
        assert "Nerfed Cover 3" in changelog["combined_notes"]
        assert changelog["meta_diff"]["from_strategies"] == ["Cover 3"]
        assert changelog["meta_diff"]["to_strategies"] == ["Gun Trips"]

    def test_unknown_patch_raises(self):
        with pytest.raises(ValueError, match="not fully found"):
            meta_version_engine.get_patch_changelog("madden26", "1.00", "1.01")

    def test_reversed_range_raises(self):
        meta_version_engine.create_snapshot("madden26", "1.03", changelog_notes=["a"])
        meta_version_engine.create_snapshot("madden26", "1.04", changelog_notes=["b"])

        with pytest.raises(ValueError, match="must precede"):
            meta_version_engine.get_patch_changelog("madden26", "1.04", "1.03")

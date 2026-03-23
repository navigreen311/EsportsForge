"""Tests for Cross-Title Cognitive Transfer Engine."""

from __future__ import annotations

import pytest

from app.schemas.cross_title import (
    CognitiveSkill,
    SkillCategory,
    TransferGrade,
)
from app.services.backbone.cross_title_transfer import CrossTitleTransfer, _profiles


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_profiles():
    """Clear in-memory profiles before each test."""
    _profiles.clear()
    yield


@pytest.fixture
def engine() -> CrossTitleTransfer:
    return CrossTitleTransfer()


# ---------------------------------------------------------------------------
# Transfer Map
# ---------------------------------------------------------------------------

class TestTransferMap:
    def test_get_all_mappings(self, engine: CrossTitleTransfer):
        maps = engine.get_transfer_map()
        assert len(maps) > 0

    def test_filter_by_from_title(self, engine: CrossTitleTransfer):
        maps = engine.get_transfer_map(from_title="madden26")
        assert all(
            m.from_title in ("madden26", "any") for m in maps
        )

    def test_filter_by_title_pair(self, engine: CrossTitleTransfer):
        maps = engine.get_transfer_map(from_title="madden26", to_title="cfb26")
        assert len(maps) > 0
        for m in maps:
            assert m.from_title in ("madden26", "any")
            assert m.to_title in ("cfb26", "any")

    def test_transfer_map_has_required_fields(self, engine: CrossTitleTransfer):
        maps = engine.get_transfer_map()
        for m in maps:
            assert m.skill
            assert m.category
            assert 0.0 <= m.transfer_rate <= 1.0


# ---------------------------------------------------------------------------
# Transfer Estimate
# ---------------------------------------------------------------------------

class TestEstimateTransfer:
    def test_known_skill(self, engine: CrossTitleTransfer):
        result = engine.estimate_transfer("madden26", "cfb26", "Pre-snap reads")
        assert result is not None
        assert result.transfer_grade == TransferGrade.DIRECT
        assert result.transfer_rate >= 0.9

    def test_unknown_skill(self, engine: CrossTitleTransfer):
        result = engine.estimate_transfer("madden26", "cfb26", "Nonexistent Skill")
        assert result is None

    def test_universal_skill(self, engine: CrossTitleTransfer):
        result = engine.estimate_transfer("madden26", "fc25", "Tilt management")
        assert result is not None
        assert result.transfer_grade == TransferGrade.DIRECT


# ---------------------------------------------------------------------------
# Cross-Title Profile
# ---------------------------------------------------------------------------

class TestCrossTitleProfile:
    def test_new_profile(self, engine: CrossTitleTransfer):
        profile = engine.get_cross_title_profile("user1")
        assert profile.user_id == "user1"
        assert profile.titles_played == []

    def test_update_profile(self, engine: CrossTitleTransfer):
        skills = [
            CognitiveSkill(
                skill_id="s1", name="Reads", category=SkillCategory.PATTERN_RECOGNITION,
                titles=["madden26"], proficiency=0.9,
            ),
            CognitiveSkill(
                skill_id="s2", name="Clock Mgmt", category=SkillCategory.DECISION_SPEED,
                titles=["madden26"], proficiency=0.7,
            ),
        ]
        profile = engine.update_profile("user1", titles=["madden26"], skills=skills)
        assert profile.titles_played == ["madden26"]
        assert len(profile.cognitive_skills) == 2
        assert profile.strongest_category == SkillCategory.PATTERN_RECOGNITION
        assert profile.weakest_category == SkillCategory.DECISION_SPEED

    def test_profile_persists(self, engine: CrossTitleTransfer):
        engine.update_profile("user1", titles=["madden26", "cfb26"])
        profile = engine.get_cross_title_profile("user1")
        assert "cfb26" in profile.titles_played


# ---------------------------------------------------------------------------
# Accelerate Onboarding
# ---------------------------------------------------------------------------

class TestAccelerateOnboarding:
    def test_onboarding_with_existing_title(self, engine: CrossTitleTransfer):
        engine.update_profile("user1", titles=["madden26"])
        plan = engine.accelerate_onboarding("user1", "cfb26")
        assert plan.user_id == "user1"
        assert plan.to_title == "cfb26"
        assert plan.from_title == "madden26"
        assert len(plan.transferable_skills) > 0
        assert plan.head_start_percentage > 0

    def test_onboarding_no_prior_titles(self, engine: CrossTitleTransfer):
        plan = engine.accelerate_onboarding("user1", "madden26")
        assert plan.from_title == "any"
        assert len(plan.skills_to_learn) > 0

    def test_onboarding_has_priority_order(self, engine: CrossTitleTransfer):
        engine.update_profile("user1", titles=["madden26"])
        plan = engine.accelerate_onboarding("user1", "cfb26")
        assert len(plan.priority_order) > 0

    def test_onboarding_estimated_hours(self, engine: CrossTitleTransfer):
        engine.update_profile("user1", titles=["madden26"])
        plan = engine.accelerate_onboarding("user1", "cfb26")
        assert plan.estimated_onboarding_hours > 0

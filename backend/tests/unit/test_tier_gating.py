"""Tests for subscription tier enforcement logic."""

from __future__ import annotations

import pytest

from app.core.tier_gating import (
    ALL_TITLES,
    TIER_FEATURES,
    TIER_ORDER,
    _tier_level,
    check_feature_access,
    check_title_access,
)
from app.models.user import TIER_TITLE_LIMITS, UserTier


# ---------------------------------------------------------------------------
# Helpers — lightweight fake User for unit tests (no DB needed)
# ---------------------------------------------------------------------------

class FakeUser:
    """Minimal User stand-in for testing tier gating logic."""

    def __init__(self, tier: UserTier, active_title: str | None = None):
        self.tier = tier
        self.active_title = active_title
        self.id = "test-user-id"


# ---------------------------------------------------------------------------
# Tier ordering
# ---------------------------------------------------------------------------

class TestTierOrdering:
    def test_tier_order_length(self):
        assert len(TIER_ORDER) == 4

    def test_free_is_lowest(self):
        assert _tier_level(UserTier.FREE) == 0

    def test_team_is_highest(self):
        assert _tier_level(UserTier.TEAM) == 3

    def test_competitive_above_free(self):
        assert _tier_level(UserTier.COMPETITIVE) > _tier_level(UserTier.FREE)

    def test_elite_above_competitive(self):
        assert _tier_level(UserTier.ELITE) > _tier_level(UserTier.COMPETITIVE)

    def test_team_above_elite(self):
        assert _tier_level(UserTier.TEAM) > _tier_level(UserTier.ELITE)


# ---------------------------------------------------------------------------
# Title access
# ---------------------------------------------------------------------------

class TestTitleAccess:
    def test_free_user_first_title_allowed(self):
        user = FakeUser(UserTier.FREE, active_title=None)
        assert check_title_access(user, "madden26") is True

    def test_free_user_active_title_allowed(self):
        user = FakeUser(UserTier.FREE, active_title="madden26")
        assert check_title_access(user, "madden26") is True

    def test_free_user_different_title_denied(self):
        user = FakeUser(UserTier.FREE, active_title="madden26")
        assert check_title_access(user, "cfb26") is False

    def test_elite_user_any_title_allowed(self):
        user = FakeUser(UserTier.ELITE, active_title="madden26")
        for title in ALL_TITLES:
            assert check_title_access(user, title) is True

    def test_team_user_any_title_allowed(self):
        user = FakeUser(UserTier.TEAM, active_title="cfb26")
        for title in ALL_TITLES:
            assert check_title_access(user, title) is True

    def test_title_limits_match_spec(self):
        assert TIER_TITLE_LIMITS[UserTier.FREE] == 1
        assert TIER_TITLE_LIMITS[UserTier.COMPETITIVE] == 3
        assert TIER_TITLE_LIMITS[UserTier.ELITE] is None
        assert TIER_TITLE_LIMITS[UserTier.TEAM] is None

    def test_all_titles_count(self):
        assert len(ALL_TITLES) == 11


# ---------------------------------------------------------------------------
# Feature access
# ---------------------------------------------------------------------------

class TestFeatureAccess:
    def test_free_has_basic_gameplan(self):
        user = FakeUser(UserTier.FREE)
        assert check_feature_access(user, "basic_gameplan") is True

    def test_free_has_meta_alerts(self):
        user = FakeUser(UserTier.FREE)
        assert check_feature_access(user, "meta_alerts") is True

    def test_free_no_player_twin(self):
        user = FakeUser(UserTier.FREE)
        assert check_feature_access(user, "player_twin") is False

    def test_free_no_film_ai(self):
        user = FakeUser(UserTier.FREE)
        assert check_feature_access(user, "film_ai") is False

    def test_competitive_has_player_twin(self):
        user = FakeUser(UserTier.COMPETITIVE)
        assert check_feature_access(user, "player_twin") is True

    def test_competitive_has_film_ai(self):
        user = FakeUser(UserTier.COMPETITIVE)
        assert check_feature_access(user, "film_ai") is True

    def test_competitive_has_tilt_guard(self):
        user = FakeUser(UserTier.COMPETITIVE)
        assert check_feature_access(user, "tilt_guard") is True

    def test_competitive_has_benchmark_ai(self):
        user = FakeUser(UserTier.COMPETITIVE)
        assert check_feature_access(user, "benchmark_ai") is True

    def test_competitive_has_install_ai(self):
        user = FakeUser(UserTier.COMPETITIVE)
        assert check_feature_access(user, "install_ai") is True

    def test_competitive_no_tourna_ops(self):
        user = FakeUser(UserTier.COMPETITIVE)
        assert check_feature_access(user, "tourna_ops") is False

    def test_elite_has_tourna_ops(self):
        user = FakeUser(UserTier.ELITE)
        assert check_feature_access(user, "tourna_ops") is True

    def test_elite_has_voice_forge(self):
        user = FakeUser(UserTier.ELITE)
        assert check_feature_access(user, "voice_forge") is True

    def test_elite_has_forge_vault(self):
        user = FakeUser(UserTier.ELITE)
        assert check_feature_access(user, "forge_vault") is True

    def test_elite_has_impact_rank_priority(self):
        user = FakeUser(UserTier.ELITE)
        assert check_feature_access(user, "impact_rank_priority") is True

    def test_elite_no_coach_portal(self):
        user = FakeUser(UserTier.ELITE)
        assert check_feature_access(user, "coach_portal") is False

    def test_team_has_coach_portal(self):
        user = FakeUser(UserTier.TEAM)
        assert check_feature_access(user, "coach_portal") is True

    def test_team_has_war_room(self):
        user = FakeUser(UserTier.TEAM)
        assert check_feature_access(user, "war_room") is True

    def test_team_has_squad_ops(self):
        user = FakeUser(UserTier.TEAM)
        assert check_feature_access(user, "squad_ops") is True

    def test_team_has_shared_playbooks(self):
        user = FakeUser(UserTier.TEAM)
        assert check_feature_access(user, "shared_playbooks") is True

    def test_unknown_feature_denied(self):
        user = FakeUser(UserTier.TEAM)
        assert check_feature_access(user, "nonexistent_feature") is False


# ---------------------------------------------------------------------------
# Tier features are cumulative
# ---------------------------------------------------------------------------

class TestTierCumulative:
    def test_competitive_includes_all_free_features(self):
        free = TIER_FEATURES[UserTier.FREE]
        competitive = TIER_FEATURES[UserTier.COMPETITIVE]
        assert free.issubset(competitive)

    def test_elite_includes_all_competitive_features(self):
        competitive = TIER_FEATURES[UserTier.COMPETITIVE]
        elite = TIER_FEATURES[UserTier.ELITE]
        assert competitive.issubset(elite)

    def test_team_includes_all_elite_features(self):
        elite = TIER_FEATURES[UserTier.ELITE]
        team = TIER_FEATURES[UserTier.TEAM]
        assert elite.issubset(team)

"""Unit tests for UFC 5 OnlineCareer Forge — build optimizer, perk rankings, style paths."""

from __future__ import annotations

import pytest

from app.schemas.ufc5.combat import (
    ArchetypeStyle,
    FighterBuild,
    FighterStylePath,
    PerkRanking,
)
from app.services.agents.ufc5.online_career import OnlineCareerForge


@pytest.fixture
def career_forge() -> OnlineCareerForge:
    return OnlineCareerForge()


# ---------------------------------------------------------------------------
# Perk Rankings
# ---------------------------------------------------------------------------


class TestPerkRankings:
    def test_returns_all_perks(self, career_forge: OnlineCareerForge) -> None:
        perks = career_forge.get_perk_rankings()
        assert len(perks) > 10
        for perk in perks:
            assert isinstance(perk, PerkRanking)
            assert perk.tier in ("S", "A", "B", "C", "D")

    def test_s_tier_perks_ranked_first(self, career_forge: OnlineCareerForge) -> None:
        perks = career_forge.get_perk_rankings()
        s_tier_found = False
        for perk in perks:
            if perk.tier == "S":
                s_tier_found = True
            elif s_tier_found and perk.tier != "S":
                # Once we leave S tier, we shouldn't go back
                break

    def test_filter_by_style_prioritizes_synergy(self, career_forge: OnlineCareerForge) -> None:
        perks = career_forge.get_perk_rankings(style=ArchetypeStyle.WRESTLER)
        # First perk should synergize with wrestler
        assert ArchetypeStyle.WRESTLER in perks[0].synergy_styles

    def test_perk_has_description(self, career_forge: OnlineCareerForge) -> None:
        perks = career_forge.get_perk_rankings()
        for perk in perks:
            assert perk.description != ""
            assert perk.perk_name != ""

    def test_win_rate_impact_in_valid_range(self, career_forge: OnlineCareerForge) -> None:
        perks = career_forge.get_perk_rankings()
        for perk in perks:
            assert -0.1 <= perk.win_rate_impact <= 0.1


# ---------------------------------------------------------------------------
# Style Paths
# ---------------------------------------------------------------------------


class TestStylePaths:
    def test_returns_style_paths(self, career_forge: OnlineCareerForge) -> None:
        paths = career_forge.get_style_paths()
        assert len(paths) > 5
        for path in paths:
            assert isinstance(path, FighterStylePath)
            assert 0.0 <= path.win_rate <= 1.0

    def test_sorted_by_win_rate_descending(self, career_forge: OnlineCareerForge) -> None:
        paths = career_forge.get_style_paths()
        for i in range(len(paths) - 1):
            assert paths[i].win_rate >= paths[i + 1].win_rate

    def test_filter_by_weight_class(self, career_forge: OnlineCareerForge) -> None:
        paths = career_forge.get_style_paths(weight_class="lightweight")
        assert len(paths) > 0
        for path in paths:
            assert path.weight_class == "lightweight"

    def test_style_path_has_perks(self, career_forge: OnlineCareerForge) -> None:
        paths = career_forge.get_style_paths()
        for path in paths:
            assert len(path.recommended_perks) > 0

    def test_style_path_has_attributes(self, career_forge: OnlineCareerForge) -> None:
        paths = career_forge.get_style_paths()
        for path in paths:
            assert len(path.key_attributes) > 0

    def test_wrestler_lightweight_has_high_win_rate(self, career_forge: OnlineCareerForge) -> None:
        paths = career_forge.get_style_paths(weight_class="lightweight")
        wrestler_paths = [p for p in paths if p.style == ArchetypeStyle.WRESTLER]
        assert len(wrestler_paths) > 0
        assert wrestler_paths[0].win_rate >= 0.55


# ---------------------------------------------------------------------------
# Fighter Builds
# ---------------------------------------------------------------------------


class TestFighterBuilds:
    def test_build_creates_valid_fighter(self, career_forge: OnlineCareerForge) -> None:
        build = career_forge.build_fighter(
            name="Test Fighter",
            weight_class="lightweight",
            style=ArchetypeStyle.WRESTLER,
        )
        assert isinstance(build, FighterBuild)
        assert build.name == "Test Fighter"
        assert build.weight_class == "lightweight"
        assert build.archetype.style == ArchetypeStyle.WRESTLER

    def test_build_has_perks(self, career_forge: OnlineCareerForge) -> None:
        build = career_forge.build_fighter(
            name="Perk Test",
            weight_class="welterweight",
            style=ArchetypeStyle.COUNTER,
        )
        assert len(build.equipped_perks) > 0
        assert len(build.equipped_perks) <= 5

    def test_build_has_strengths_and_weaknesses(self, career_forge: OnlineCareerForge) -> None:
        build = career_forge.build_fighter(
            name="S/W Test",
            weight_class="middleweight",
            style=ArchetypeStyle.KICKBOXER,
        )
        assert len(build.strengths) > 0
        assert len(build.weaknesses) > 0

    def test_build_has_matchup_notes(self, career_forge: OnlineCareerForge) -> None:
        build = career_forge.build_fighter(
            name="Matchup Test",
            weight_class="heavyweight",
            style=ArchetypeStyle.BRAWLER,
        )
        assert len(build.matchup_notes) > 0

    def test_build_overall_rating_is_reasonable(self, career_forge: OnlineCareerForge) -> None:
        build = career_forge.build_fighter(
            name="Rating Test",
            weight_class="lightweight",
            style=ArchetypeStyle.GRAPPLER,
        )
        assert 50.0 <= build.overall_rating <= 100.0


# ---------------------------------------------------------------------------
# Build Comparison
# ---------------------------------------------------------------------------


class TestBuildComparison:
    def test_compare_two_builds(self, career_forge: OnlineCareerForge) -> None:
        build_a = career_forge.build_fighter("Fighter A", "lightweight", ArchetypeStyle.WRESTLER)
        build_b = career_forge.build_fighter("Fighter B", "lightweight", ArchetypeStyle.BRAWLER)
        result = career_forge.compare_builds(build_a, build_b)
        assert result["build_a"] == "Fighter A"
        assert result["build_b"] == "Fighter B"
        assert "advantage" in result
        assert result["advantage"] in ("Fighter A", "Fighter B")

    def test_compare_same_style(self, career_forge: OnlineCareerForge) -> None:
        build_a = career_forge.build_fighter("A", "lightweight", ArchetypeStyle.COUNTER)
        build_b = career_forge.build_fighter("B", "lightweight", ArchetypeStyle.COUNTER)
        result = career_forge.compare_builds(build_a, build_b)
        assert result["win_rate_a"] == result["win_rate_b"]

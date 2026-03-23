"""Tests for ProofAI — evidence generation, comparable cases, briefing summaries."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.schemas.drill import (
    ComparableCase,
    Evidence,
    EvidenceType,
    ProofPackage,
)
from app.services.backbone.proof_ai import (
    ProofAI,
    _case_store,
    _clear_cases,
    _seed_cases,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_state():
    """Reset case store between tests."""
    _clear_cases()
    yield
    _clear_cases()


@pytest.fixture
def ai() -> ProofAI:
    return ProofAI()


@pytest.fixture
def sample_recommendation() -> dict:
    return {
        "id": str(uuid4()),
        "agent_name": "ImpactRank",
        "content": "Switch to man coverage against this opponent",
        "data": {
            "stats": {"pass_success_rate": 0.35, "man_coverage_rate": 0.12},
            "patterns": ["Opponent throws short passes", "Zone is being exploited"],
            "history": ["Lost 3 of last 5 with zone coverage"],
            "weakness": "Zone coverage breakdowns",
            "win_rate_impact": 0.15,
        },
        "situation": {
            "title": "madden26",
            "type": "defensive_adjustment",
            "tags": ["coverage", "passing_defense"],
        },
        "player_data": {"skill_level": 0.6},
    }


@pytest.fixture
def seeded_cases():
    """Seed comparable case store with test data."""
    cases = [
        {
            "title": "madden26",
            "situation": "Opponent exploiting zone coverage",
            "action": "Switched to man coverage with safety help",
            "outcome": "Reduced opponent completion rate from 72% to 48%",
            "tags": ["coverage", "passing_defense"],
            "skill_level": 0.55,
            "source": "historical_data",
        },
        {
            "title": "madden26",
            "situation": "High opponent short pass rate",
            "action": "Added underneath coverage with linebackers",
            "outcome": "Forced 2 interceptions in next game",
            "tags": ["coverage", "short_passing"],
            "skill_level": 0.65,
            "source": "historical_data",
        },
        {
            "title": "cfb26",
            "situation": "Spread offense giving trouble",
            "action": "Switched to nickel formation",
            "outcome": "Held opponent to 10 points",
            "tags": ["formation", "spread_defense"],
            "skill_level": 0.4,
            "source": "historical_data",
        },
    ]
    _seed_cases(cases)
    return cases


# ---------------------------------------------------------------------------
# generate_proof tests
# ---------------------------------------------------------------------------

class TestGenerateProof:
    def test_returns_proof_package(self, ai: ProofAI, sample_recommendation: dict):
        proof = ai.generate_proof(sample_recommendation)

        assert isinstance(proof, ProofPackage)
        assert proof.recommendation_summary == "Switch to man coverage against this opponent"

    def test_includes_statistical_evidence(self, ai: ProofAI, sample_recommendation: dict):
        proof = ai.generate_proof(sample_recommendation)
        stat_evidence = [e for e in proof.evidence if e.evidence_type == EvidenceType.STATISTICAL]
        assert len(stat_evidence) >= 1
        assert stat_evidence[0].data_points  # Has data points

    def test_includes_pattern_evidence(self, ai: ProofAI, sample_recommendation: dict):
        proof = ai.generate_proof(sample_recommendation)
        pattern_evidence = [e for e in proof.evidence if e.evidence_type == EvidenceType.PATTERN]
        assert len(pattern_evidence) >= 1

    def test_includes_historical_evidence(self, ai: ProofAI, sample_recommendation: dict):
        proof = ai.generate_proof(sample_recommendation)
        hist_evidence = [e for e in proof.evidence if e.evidence_type == EvidenceType.HISTORICAL]
        assert len(hist_evidence) >= 1

    def test_extracts_reason_from_win_rate_impact(self, ai: ProofAI, sample_recommendation: dict):
        proof = ai.generate_proof(sample_recommendation)
        assert "win rate" in proof.reason.lower()

    def test_fallback_evidence_when_no_data(self, ai: ProofAI):
        bare_rec = {"content": "Do something", "agent_name": "TestAgent"}
        proof = ai.generate_proof(bare_rec)
        assert len(proof.evidence) >= 1
        assert proof.evidence[0].evidence_type == EvidenceType.EXPERT_HEURISTIC

    def test_overall_evidence_strength_is_calculated(self, ai: ProofAI, sample_recommendation: dict):
        proof = ai.generate_proof(sample_recommendation)
        assert 0.0 < proof.overall_evidence_strength <= 1.0

    def test_briefing_summary_is_populated(self, ai: ProofAI, sample_recommendation: dict):
        proof = ai.generate_proof(sample_recommendation)
        assert "EVIDENCE BRIEFING" in proof.briefing_summary
        assert "RECOMMENDATION" in proof.briefing_summary


# ---------------------------------------------------------------------------
# find_comparable_cases tests
# ---------------------------------------------------------------------------

class TestFindComparableCases:
    def test_no_cases_returns_empty(self, ai: ProofAI):
        result = ai.find_comparable_cases({"title": "madden26"}, {"skill_level": 0.5})
        assert result == []

    def test_finds_matching_cases(self, ai: ProofAI, seeded_cases):
        situation = {
            "title": "madden26",
            "type": "defensive_adjustment",
            "tags": ["coverage", "passing_defense"],
        }
        result = ai.find_comparable_cases(situation, {"skill_level": 0.6})

        assert len(result) >= 1
        assert all(isinstance(c, ComparableCase) for c in result)

    def test_cases_sorted_by_similarity(self, ai: ProofAI, seeded_cases):
        situation = {
            "title": "madden26",
            "tags": ["coverage", "passing_defense"],
        }
        result = ai.find_comparable_cases(situation, {"skill_level": 0.6})

        if len(result) >= 2:
            assert result[0].similarity_score >= result[1].similarity_score

    def test_max_cases_limited(self, ai: ProofAI):
        # Seed 10 similar cases
        cases = [
            {
                "title": "madden26",
                "situation": f"Case {i}",
                "action": f"Action {i}",
                "outcome": f"Outcome {i}",
                "tags": ["test"],
                "skill_level": 0.5,
            }
            for i in range(10)
        ]
        _seed_cases(cases)

        result = ai.find_comparable_cases(
            {"title": "madden26", "tags": ["test"]},
            {"skill_level": 0.5},
        )
        assert len(result) <= 5

    def test_empty_situation_returns_empty(self, ai: ProofAI, seeded_cases):
        result = ai.find_comparable_cases({}, {})
        assert result == []


# ---------------------------------------------------------------------------
# generate_evidence_summary tests
# ---------------------------------------------------------------------------

class TestGenerateEvidenceSummary:
    def test_briefing_format(self, ai: ProofAI, sample_recommendation: dict):
        proof = ai.generate_proof(sample_recommendation)
        summary = ai.generate_evidence_summary(proof)

        assert "=== EVIDENCE BRIEFING ===" in summary
        assert "=== END BRIEFING ===" in summary
        assert "RECOMMENDATION:" in summary
        assert "CORE REASON:" in summary
        assert "EVIDENCE STRENGTH:" in summary

    def test_includes_evidence_items(self, ai: ProofAI, sample_recommendation: dict):
        proof = ai.generate_proof(sample_recommendation)
        summary = ai.generate_evidence_summary(proof)

        assert "SUPPORTING EVIDENCE:" in summary

    def test_strength_label_strong(self, ai: ProofAI):
        proof = ProofPackage(
            recommendation_id=uuid4(),
            recommendation_summary="Test",
            reason="Test reason",
            overall_evidence_strength=0.8,
        )
        summary = ai.generate_evidence_summary(proof)
        assert "STRONG" in summary

    def test_strength_label_moderate(self, ai: ProofAI):
        proof = ProofPackage(
            recommendation_id=uuid4(),
            recommendation_summary="Test",
            reason="Test reason",
            overall_evidence_strength=0.5,
        )
        summary = ai.generate_evidence_summary(proof)
        assert "MODERATE" in summary

    def test_strength_label_weak(self, ai: ProofAI):
        proof = ProofPackage(
            recommendation_id=uuid4(),
            recommendation_summary="Test",
            reason="Test reason",
            overall_evidence_strength=0.2,
        )
        summary = ai.generate_evidence_summary(proof)
        assert "WEAK" in summary

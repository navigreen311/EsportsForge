"""ProofAI — evidence generation and comparable case analysis.

Every recommendation the platform makes must be backed by evidence.
ProofAI builds proof packages: the reason behind the recommendation,
supporting data points, and comparable historical cases. Output is
formatted for war room briefings — concise, data-driven, actionable.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID, uuid4

from app.schemas.drill import (
    ComparableCase,
    Evidence,
    EvidenceType,
    ProofPackage,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MIN_SIMILARITY_THRESHOLD = 0.3
_MAX_COMPARABLE_CASES = 5
_EVIDENCE_STRENGTH_WEIGHTS = {
    EvidenceType.STATISTICAL: 0.9,
    EvidenceType.HISTORICAL: 0.7,
    EvidenceType.PATTERN: 0.6,
    EvidenceType.COMPARABLE_CASE: 0.5,
    EvidenceType.EXPERT_HEURISTIC: 0.4,
}

# ---------------------------------------------------------------------------
# In-memory case database (production: vector DB / ForgeDataFabric)
# ---------------------------------------------------------------------------

_case_store: list[dict] = []


def _seed_cases(cases: list[dict]) -> None:
    """Seed the case store (used by tests and bootstrap)."""
    _case_store.clear()
    _case_store.extend(cases)


def _clear_cases() -> None:
    """Clear the case store."""
    _case_store.clear()


class ProofAI:
    """Generates evidence packages for recommendations.

    Combines statistical evidence, pattern analysis, and comparable
    historical cases into a single proof package formatted for
    war room briefings.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def generate_proof(self, recommendation: dict) -> ProofPackage:
        """Build a complete evidence package for a recommendation.

        Parameters
        ----------
        recommendation:
            Dict with at least 'id', 'content', 'agent_name', 'data'.
            Optional: 'player_data', 'situation'.

        Returns
        -------
        ProofPackage
            Complete evidence + comparable cases + briefing summary.
        """
        rec_id = recommendation.get("id", uuid4())
        if isinstance(rec_id, str):
            rec_id = UUID(rec_id)

        content = recommendation.get("content", "")
        data = recommendation.get("data", {})
        player_data = recommendation.get("player_data", {})
        situation = recommendation.get("situation", {})

        # Build core reason
        reason = self._extract_reason(recommendation)

        # Gather evidence from multiple sources
        evidence = self._gather_evidence(recommendation, data)

        # Find comparable cases
        comparable = self.find_comparable_cases(situation, player_data)

        # Calculate overall evidence strength
        overall_strength = self._calculate_overall_strength(evidence, comparable)

        # Build proof package
        proof = ProofPackage(
            recommendation_id=rec_id,
            recommendation_summary=content,
            reason=reason,
            evidence=evidence,
            comparable_cases=comparable,
            overall_evidence_strength=round(overall_strength, 4),
        )

        # Generate briefing summary
        proof.briefing_summary = self.generate_evidence_summary(proof)

        logger.info(
            "ProofAI: generated proof for rec %s — %d evidence items, "
            "%d comparable cases, strength=%.2f",
            rec_id, len(evidence), len(comparable), overall_strength,
        )
        return proof

    # ------------------------------------------------------------------
    # Comparable cases
    # ------------------------------------------------------------------

    def find_comparable_cases(
        self,
        situation: dict,
        player_data: dict,
    ) -> list[ComparableCase]:
        """Find historical situations similar to the current one.

        Parameters
        ----------
        situation:
            Dict describing the current situation (e.g. game state,
            opponent tendencies, score context).
        player_data:
            Dict with player stats and history.

        Returns
        -------
        list[ComparableCase]
            Up to 5 comparable cases sorted by similarity.
        """
        if not situation and not player_data:
            return []

        matches: list[ComparableCase] = []

        for case in _case_store:
            similarity = self._compute_similarity(situation, player_data, case)
            if similarity >= _MIN_SIMILARITY_THRESHOLD:
                matches.append(ComparableCase(
                    situation_summary=case.get("situation", "Unknown situation"),
                    action_taken=case.get("action", "Unknown action"),
                    outcome=case.get("outcome", "Unknown outcome"),
                    similarity_score=round(similarity, 4),
                    source=case.get("source", "historical_data"),
                ))

        # Sort by similarity descending, take top N
        matches.sort(key=lambda c: c.similarity_score, reverse=True)
        return matches[:_MAX_COMPARABLE_CASES]

    # ------------------------------------------------------------------
    # Evidence summary (war room briefing)
    # ------------------------------------------------------------------

    def generate_evidence_summary(self, proof: ProofPackage) -> str:
        """Generate a war room briefing format summary.

        Parameters
        ----------
        proof:
            The proof package to summarize.

        Returns
        -------
        str
            Concise briefing-style summary.
        """
        lines: list[str] = []

        # Header
        lines.append("=== EVIDENCE BRIEFING ===")
        lines.append("")

        # Recommendation
        lines.append(f"RECOMMENDATION: {proof.recommendation_summary}")
        lines.append(f"CORE REASON: {proof.reason}")
        lines.append("")

        # Evidence strength
        strength_label = (
            "STRONG" if proof.overall_evidence_strength >= 0.7
            else "MODERATE" if proof.overall_evidence_strength >= 0.4
            else "WEAK"
        )
        lines.append(
            f"EVIDENCE STRENGTH: {strength_label} "
            f"({proof.overall_evidence_strength:.0%})"
        )
        lines.append("")

        # Supporting evidence
        if proof.evidence:
            lines.append("SUPPORTING EVIDENCE:")
            for i, ev in enumerate(proof.evidence, 1):
                lines.append(f"  {i}. [{ev.evidence_type.value.upper()}] {ev.title}")
                if ev.data_points:
                    for dp in ev.data_points[:3]:  # Cap at 3 per evidence
                        lines.append(f"     - {dp}")
            lines.append("")

        # Comparable cases
        if proof.comparable_cases:
            lines.append("COMPARABLE CASES:")
            for i, case in enumerate(proof.comparable_cases, 1):
                lines.append(
                    f"  {i}. {case.situation_summary} "
                    f"(similarity: {case.similarity_score:.0%})"
                )
                lines.append(f"     Action: {case.action_taken}")
                lines.append(f"     Outcome: {case.outcome}")
            lines.append("")

        lines.append("=== END BRIEFING ===")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_reason(recommendation: dict) -> str:
        """Extract or generate the core reason for a recommendation."""
        # Check explicit reason
        if recommendation.get("reason"):
            return recommendation["reason"]

        # Derive from data
        data = recommendation.get("data", {})
        content = recommendation.get("content", "")

        if data.get("win_rate_impact"):
            return (
                f"This change is projected to improve win rate by "
                f"{data['win_rate_impact']:.1%}."
            )
        if data.get("weakness"):
            return f"Addresses identified weakness: {data['weakness']}."
        if content:
            return f"Based on analysis: {content[:200]}"

        return "Recommendation generated from available data."

    def _gather_evidence(
        self,
        recommendation: dict,
        data: dict,
    ) -> list[Evidence]:
        """Collect evidence from recommendation data."""
        evidence: list[Evidence] = []

        # Statistical evidence from data
        if data.get("stats"):
            stats = data["stats"]
            data_points = [f"{k}: {v}" for k, v in stats.items()]
            evidence.append(Evidence(
                evidence_type=EvidenceType.STATISTICAL,
                title="Performance Statistics",
                detail="Statistical analysis of player performance data.",
                data_points=data_points,
                strength=0.8,
            ))

        # Pattern evidence
        if data.get("patterns"):
            patterns = data["patterns"]
            if isinstance(patterns, list):
                evidence.append(Evidence(
                    evidence_type=EvidenceType.PATTERN,
                    title="Detected Patterns",
                    detail="Recurring patterns identified in gameplay.",
                    data_points=patterns[:5],
                    strength=0.6,
                ))

        # Historical evidence
        if data.get("history"):
            history = data["history"]
            data_points = (
                history if isinstance(history, list)
                else [str(history)]
            )
            evidence.append(Evidence(
                evidence_type=EvidenceType.HISTORICAL,
                title="Historical Performance",
                detail="Historical trends supporting this recommendation.",
                data_points=data_points[:5],
                strength=0.7,
            ))

        # Expert heuristic if no other evidence
        if not evidence:
            agent = recommendation.get("agent_name", "AI")
            evidence.append(Evidence(
                evidence_type=EvidenceType.EXPERT_HEURISTIC,
                title="AI Analysis",
                detail=f"Recommendation from {agent} based on general game knowledge.",
                data_points=[recommendation.get("content", "General recommendation.")],
                strength=0.4,
            ))

        return evidence

    @staticmethod
    def _compute_similarity(
        situation: dict,
        player_data: dict,
        case: dict,
    ) -> float:
        """Compute similarity between current situation and a stored case.

        Uses a simple weighted key-overlap heuristic. Production would
        use embedding similarity via a vector DB.
        """
        if not case:
            return 0.0

        score = 0.0
        comparisons = 0

        case_tags = set(case.get("tags", []))
        situation_tags = set()

        # Extract tags from situation
        if situation.get("type"):
            situation_tags.add(situation["type"])
        if situation.get("tags"):
            situation_tags.update(situation["tags"])

        # Tag overlap
        if case_tags and situation_tags:
            overlap = len(case_tags & situation_tags)
            total = len(case_tags | situation_tags)
            if total > 0:
                score += overlap / total
            comparisons += 1

        # Title match
        if situation.get("title") and case.get("title"):
            if situation["title"] == case["title"]:
                score += 1.0
            comparisons += 1

        # Skill level proximity
        player_level = player_data.get("skill_level", 0.5)
        case_level = case.get("skill_level", 0.5)
        level_diff = abs(player_level - case_level)
        score += max(0.0, 1.0 - level_diff * 2)
        comparisons += 1

        if comparisons == 0:
            return 0.0

        return min(1.0, score / comparisons)

    @staticmethod
    def _calculate_overall_strength(
        evidence: list[Evidence],
        comparable: list[ComparableCase],
    ) -> float:
        """Calculate aggregate evidence strength."""
        if not evidence and not comparable:
            return 0.0

        total = 0.0
        count = 0

        for ev in evidence:
            weight = _EVIDENCE_STRENGTH_WEIGHTS.get(ev.evidence_type, 0.5)
            total += ev.strength * weight
            count += 1

        for case in comparable:
            total += case.similarity_score * 0.5
            count += 1

        return min(1.0, total / max(1, count))

"""Cross-Title Cognitive Transfer Engine.

Maps cognitive skills across game titles, estimates transfer rates,
builds cross-title player profiles, and accelerates onboarding
into new titles by leveraging existing cognitive strengths.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import structlog

from app.schemas.cross_title import (
    CognitiveSkill,
    CrossTitleProfile,
    SkillCategory,
    TitleSwitch,
    TransferGrade,
    TransferMap,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Transfer knowledge base — which skills transfer between titles
# ---------------------------------------------------------------------------
# Format: (from_title, to_title, skill_name, category, grade, rate, notes, hours)
TRANSFER_KNOWLEDGE: list[tuple[str, str, str, SkillCategory, TransferGrade, float, str, float]] = [
    # Madden <-> CFB
    ("madden26", "cfb26", "Pre-snap reads", SkillCategory.PATTERN_RECOGNITION, TransferGrade.DIRECT, 0.95, "Nearly identical pre-snap mechanics.", 2.0),
    ("madden26", "cfb26", "Play calling", SkillCategory.STRATEGIC, TransferGrade.HIGH, 0.80, "Playbook structures differ but concepts transfer.", 8.0),
    ("madden26", "cfb26", "Clock management", SkillCategory.DECISION_SPEED, TransferGrade.DIRECT, 0.92, "Same core clock rules apply.", 1.0),
    ("madden26", "cfb26", "User coverage", SkillCategory.MECHANICAL, TransferGrade.HIGH, 0.85, "Timing windows slightly different.", 5.0),
    ("madden26", "cfb26", "Opponent reading", SkillCategory.OPPONENT_READING, TransferGrade.DIRECT, 0.90, "Same behavioral cues apply.", 2.0),
    ("cfb26", "madden26", "Pre-snap reads", SkillCategory.PATTERN_RECOGNITION, TransferGrade.DIRECT, 0.95, "Nearly identical pre-snap mechanics.", 2.0),
    ("cfb26", "madden26", "Play calling", SkillCategory.STRATEGIC, TransferGrade.HIGH, 0.78, "Pro formations require adjustment.", 10.0),
    ("cfb26", "madden26", "Clock management", SkillCategory.DECISION_SPEED, TransferGrade.DIRECT, 0.92, "Same core clock rules.", 1.0),
    ("cfb26", "madden26", "User coverage", SkillCategory.MECHANICAL, TransferGrade.HIGH, 0.83, "Speed/athleticism balance differs.", 6.0),
    ("cfb26", "madden26", "Opponent reading", SkillCategory.OPPONENT_READING, TransferGrade.DIRECT, 0.90, "Same behavioral cues apply.", 2.0),
    # FPS-like cross-genre skills
    ("madden26", "fc25", "Reaction time", SkillCategory.REACTION_TIME, TransferGrade.MODERATE, 0.60, "Different input types but raw reaction transfers.", 15.0),
    ("madden26", "fc25", "Spatial awareness", SkillCategory.SPATIAL_AWARENESS, TransferGrade.LOW, 0.30, "Field vs pitch spatial models differ significantly.", 30.0),
    ("madden26", "fc25", "Opponent reading", SkillCategory.OPPONENT_READING, TransferGrade.MODERATE, 0.55, "Behavioral reading transfers, but sport-specific cues do not.", 20.0),
    ("madden26", "fc25", "Resource management", SkillCategory.RESOURCE_MANAGEMENT, TransferGrade.LOW, 0.25, "Stamina/substitution models are completely different.", 25.0),
    # General cognitive transfers
    ("any", "any", "Tilt management", SkillCategory.ADAPTATION, TransferGrade.DIRECT, 0.95, "Mental composure is game-agnostic.", 0.0),
    ("any", "any", "Tournament nerves", SkillCategory.ADAPTATION, TransferGrade.DIRECT, 0.90, "Pressure handling transfers across all titles.", 0.0),
    ("any", "any", "VOD review skills", SkillCategory.PATTERN_RECOGNITION, TransferGrade.HIGH, 0.80, "Analytical framework transfers, specifics need learning.", 5.0),
    ("any", "any", "Communication", SkillCategory.COMMUNICATION, TransferGrade.DIRECT, 0.95, "Team communication skills are universal.", 1.0),
]

# ---------------------------------------------------------------------------
# In-memory profile store
# ---------------------------------------------------------------------------
_profiles: dict[str, CrossTitleProfile] = {}


class CrossTitleTransfer:
    """Cross-title cognitive transfer engine."""

    # -----------------------------------------------------------------
    # Transfer Map
    # -----------------------------------------------------------------
    def get_transfer_map(
        self,
        from_title: str | None = None,
        to_title: str | None = None,
    ) -> list[TransferMap]:
        """Return transfer mappings, optionally filtered by title pair.

        If no titles specified, returns all known transfer mappings.
        """
        results: list[TransferMap] = []
        for src, dst, skill, cat, grade, rate, notes, hours in TRANSFER_KNOWLEDGE:
            if from_title and src not in (from_title, "any"):
                continue
            if to_title and dst not in (to_title, "any"):
                continue
            results.append(TransferMap(
                skill=skill,
                category=cat,
                from_title=src,
                to_title=dst,
                transfer_grade=grade,
                transfer_rate=rate,
                adaptation_notes=notes,
                estimated_hours_to_adapt=hours,
            ))
        logger.info(
            "cross_title.transfer_map",
            from_title=from_title,
            to_title=to_title,
            results=len(results),
        )
        return results

    # -----------------------------------------------------------------
    # Transfer Estimate
    # -----------------------------------------------------------------
    def estimate_transfer(
        self, from_title: str, to_title: str, skill: str
    ) -> TransferMap | None:
        """Estimate how well a specific skill transfers between two titles.

        Returns None if no mapping is known for this combination.
        """
        for src, dst, sk, cat, grade, rate, notes, hours in TRANSFER_KNOWLEDGE:
            if (
                src in (from_title, "any")
                and dst in (to_title, "any")
                and sk.lower() == skill.lower()
            ):
                return TransferMap(
                    skill=sk,
                    category=cat,
                    from_title=from_title,
                    to_title=to_title,
                    transfer_grade=grade,
                    transfer_rate=rate,
                    adaptation_notes=notes,
                    estimated_hours_to_adapt=hours,
                )
        logger.info(
            "cross_title.estimate_miss",
            from_title=from_title,
            to_title=to_title,
            skill=skill,
        )
        return None

    # -----------------------------------------------------------------
    # Cross-Title Profile
    # -----------------------------------------------------------------
    def get_cross_title_profile(self, user_id: str) -> CrossTitleProfile:
        """Return the player's cross-title cognitive profile.

        Creates a default profile if none exists.
        """
        if user_id in _profiles:
            return _profiles[user_id]

        profile = CrossTitleProfile(
            user_id=user_id,
            titles_played=[],
            cognitive_skills=[],
        )
        _profiles[user_id] = profile
        return profile

    def update_profile(
        self,
        user_id: str,
        titles: list[str] | None = None,
        skills: list[CognitiveSkill] | None = None,
    ) -> CrossTitleProfile:
        """Update a player's cross-title profile."""
        profile = self.get_cross_title_profile(user_id)
        if titles is not None:
            profile.titles_played = titles
        if skills is not None:
            profile.cognitive_skills = skills
            self._compute_profile_stats(profile)
        profile.last_assessed = datetime.utcnow()
        _profiles[user_id] = profile
        logger.info("cross_title.profile_updated", user_id=user_id)
        return profile

    # -----------------------------------------------------------------
    # Accelerate Onboarding
    # -----------------------------------------------------------------
    def accelerate_onboarding(
        self, user_id: str, new_title: str
    ) -> TitleSwitch:
        """Use existing skills to speed up learning a new title.

        Analyzes the player's profile and known transfer maps to
        build a personalized onboarding plan.
        """
        profile = self.get_cross_title_profile(user_id)

        # Find the player's strongest existing title
        from_title = self._pick_best_source_title(profile, new_title)

        # Get all relevant transfer maps
        transfers = self.get_transfer_map(from_title=from_title, to_title=new_title)
        # Also include universal transfers
        if from_title != "any":
            universal = self.get_transfer_map(from_title="any", to_title="any")
            seen_skills = {t.skill for t in transfers}
            for u in universal:
                if u.skill not in seen_skills:
                    transfers.append(u)

        # Calculate head start
        if transfers:
            avg_rate = sum(t.transfer_rate for t in transfers) / len(transfers)
            total_hours = sum(t.estimated_hours_to_adapt for t in transfers)
        else:
            avg_rate = 0.0
            total_hours = 100.0  # Default for unknown title pair

        # Determine skills that need fresh learning
        transferable_skill_names = {t.skill for t in transfers}
        # These are title-specific skills that don't transfer
        skills_to_learn = [
            f"{new_title}-specific mechanics",
            f"{new_title} meta knowledge",
            f"{new_title} matchup-specific strategies",
        ]

        # Priority order: highest transfer rate first, then hours to adapt
        sorted_transfers = sorted(
            transfers,
            key=lambda t: (-t.transfer_rate, t.estimated_hours_to_adapt),
        )
        priority_order = [t.skill for t in sorted_transfers] + skills_to_learn

        result = TitleSwitch(
            user_id=user_id,
            from_title=from_title or "none",
            to_title=new_title,
            transferable_skills=sorted_transfers,
            skills_to_learn=skills_to_learn,
            estimated_onboarding_hours=total_hours,
            head_start_percentage=min(avg_rate, 1.0),
            priority_order=priority_order,
        )
        logger.info(
            "cross_title.onboarding_plan",
            user_id=user_id,
            new_title=new_title,
            head_start=f"{avg_rate:.0%}",
        )
        return result

    # -----------------------------------------------------------------
    # Internals
    # -----------------------------------------------------------------
    @staticmethod
    def _pick_best_source_title(
        profile: CrossTitleProfile, target_title: str
    ) -> str:
        """Pick the best existing title to transfer from."""
        if not profile.titles_played:
            return "any"
        # Prefer titles that aren't the target
        candidates = [t for t in profile.titles_played if t != target_title]
        return candidates[0] if candidates else profile.titles_played[0]

    @staticmethod
    def _compute_profile_stats(profile: CrossTitleProfile) -> None:
        """Recompute aggregate stats on a profile."""
        if not profile.cognitive_skills:
            return

        # Group by category
        cat_scores: dict[SkillCategory, list[float]] = {}
        for skill in profile.cognitive_skills:
            cat_scores.setdefault(skill.category, []).append(skill.proficiency)

        cat_avgs = {
            cat: sum(scores) / len(scores)
            for cat, scores in cat_scores.items()
        }
        if cat_avgs:
            profile.strongest_category = max(cat_avgs, key=cat_avgs.get)  # type: ignore[arg-type]
            profile.weakest_category = min(cat_avgs, key=cat_avgs.get)  # type: ignore[arg-type]
            profile.versatility_score = sum(cat_avgs.values()) / len(cat_avgs)

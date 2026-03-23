"""DiamondDynastyIQ — meta lineup builder and pitching staff optimizer for MLB The Show 26.

Builds optimal Diamond Dynasty lineups based on the current meta,
optimizes pitching rotations and bullpen construction, and evaluates
card value for team building decisions.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.mlb26.hitting import (
    DDLineup,
    DDPitchingStaff,
    DDPlayerCard,
    LineupSlot,
    PitcherRole,
    RotationSlot,
    StaffAnalysis,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Meta lineup building rules
# ---------------------------------------------------------------------------

_LINEUP_ORDER_PRIORITY: dict[int, dict[str, Any]] = {
    1: {"role": "leadoff", "priority": ["speed", "contact", "obp"], "min_speed": 70, "ideal_speed": 85},
    2: {"role": "two_hole", "priority": ["contact", "obp", "speed"], "min_contact": 75},
    3: {"role": "three_hole", "priority": ["power", "contact", "clutch"], "min_power": 80},
    4: {"role": "cleanup", "priority": ["power", "clutch"], "min_power": 85},
    5: {"role": "five_hole", "priority": ["power", "contact"], "min_power": 75},
    6: {"role": "six_hole", "priority": ["contact", "fielding"], "min_contact": 70},
    7: {"role": "seven_hole", "priority": ["fielding", "contact"], "min_fielding": 70},
    8: {"role": "eight_hole", "priority": ["fielding", "speed"], "min_fielding": 65},
    9: {"role": "nine_hole", "priority": ["speed", "contact"], "notes": "Pitcher spot in NL / fast guy in DH"},
}

# Pitching staff composition rules
_STAFF_RULES: dict[str, dict[str, Any]] = {
    "starter_count": 5,
    "closer": {"min_velocity": 95, "min_h9": 80, "min_k9": 85},
    "setup": {"min_velocity": 93, "min_h9": 75, "min_k9": 80},
    "long_relief": {"min_stamina": 70, "min_control": 75},
    "matchup_lefty": {"throws": "L", "min_k9": 78},
}


class DiamondDynastyIQ:
    """MLB The Show 26 Diamond Dynasty lineup and staff builder.

    Constructs meta-optimal lineups, optimizes pitching rotations,
    and evaluates roster construction decisions.
    """

    # ------------------------------------------------------------------
    # Meta lineup builder
    # ------------------------------------------------------------------

    def build_meta_lineup(
        self,
        available_cards: list[DDPlayerCard],
        platoon_advantage: str = "vs_rhp",
    ) -> DDLineup:
        """Build the optimal 9-man lineup from available cards.

        Assigns each card to the best lineup slot based on meta priorities,
        platoon advantages, and attribute thresholds.
        """
        if not available_cards:
            return DDLineup(slots=[], notes=["No cards provided."], overall_rating=0)

        used: set[str] = set()
        slots: list[LineupSlot] = []

        for order, rules in _LINEUP_ORDER_PRIORITY.items():
            best_card = None
            best_score = -1.0

            for card in available_cards:
                if card.name in used:
                    continue
                if card.position == "P":
                    continue

                score = self._score_for_slot(card, rules, platoon_advantage)
                if score > best_score:
                    best_score = score
                    best_card = card

            if best_card:
                used.add(best_card.name)
                slots.append(LineupSlot(
                    order=order,
                    card=best_card,
                    role=rules["role"],
                    fit_score=round(best_score, 2),
                ))

        avg_ovr = sum(s.card.overall for s in slots) / max(len(slots), 1)
        notes: list[str] = []
        if avg_ovr >= 95:
            notes.append("Elite lineup — competitive at the highest level.")
        elif avg_ovr >= 90:
            notes.append("Strong lineup — should compete in most divisions.")
        else:
            notes.append("Developing lineup — prioritize upgrades at 3-hole and cleanup.")

        # Check platoon balance
        lhh = sum(1 for s in slots if s.card.bats == "L")
        rhh = sum(1 for s in slots if s.card.bats == "R")
        if lhh > 6:
            notes.append("Lineup is very left-handed heavy — vulnerable to LHP.")
        elif rhh > 6:
            notes.append("Lineup is very right-handed heavy — consider switch hitters.")

        return DDLineup(
            slots=slots,
            notes=notes,
            overall_rating=round(avg_ovr, 1),
            platoon=platoon_advantage,
        )

    # ------------------------------------------------------------------
    # Pitching staff optimizer
    # ------------------------------------------------------------------

    def optimize_pitching_staff(
        self,
        available_pitchers: list[DDPlayerCard],
    ) -> DDPitchingStaff:
        """Build an optimal pitching rotation and bullpen.

        Assigns pitchers to roles (SP, closer, setup, long relief, matchup)
        based on attribute thresholds and meta priorities.
        """
        starters: list[RotationSlot] = []
        bullpen: list[RotationSlot] = []
        used: set[str] = set()

        # Sort by overall for starters
        sp_candidates = sorted(
            [p for p in available_pitchers if p.position in ("SP", "P") and p.stamina >= 65],
            key=lambda p: p.overall,
            reverse=True,
        )

        for i, pitcher in enumerate(sp_candidates[:5]):
            used.add(pitcher.name)
            starters.append(RotationSlot(
                card=pitcher,
                role=PitcherRole.STARTER,
                order=i + 1,
                notes=f"SP{i + 1}: {pitcher.overall} OVR, {pitcher.velocity} velo",
            ))

        # Bullpen assignment
        bp_candidates = [p for p in available_pitchers if p.name not in used]
        bp_candidates.sort(key=lambda p: p.overall, reverse=True)

        # Closer
        closer_candidates = [
            p for p in bp_candidates
            if p.velocity >= 93 and p.k_per_9 >= 80
        ]
        if closer_candidates:
            closer = closer_candidates[0]
            used.add(closer.name)
            bullpen.append(RotationSlot(
                card=closer,
                role=PitcherRole.CLOSER,
                order=1,
                notes=f"Closer: {closer.velocity} velo, {closer.k_per_9} K/9",
            ))

        # Setup
        setup_candidates = [p for p in bp_candidates if p.name not in used and p.velocity >= 91]
        for i, pitcher in enumerate(setup_candidates[:2]):
            used.add(pitcher.name)
            bullpen.append(RotationSlot(
                card=pitcher,
                role=PitcherRole.SETUP,
                order=i + 2,
                notes=f"Setup: {pitcher.overall} OVR",
            ))

        # Long relief
        lr_candidates = [p for p in bp_candidates if p.name not in used and p.stamina >= 55]
        if lr_candidates:
            lr = lr_candidates[0]
            used.add(lr.name)
            bullpen.append(RotationSlot(
                card=lr,
                role=PitcherRole.LONG_RELIEF,
                order=len(bullpen) + 1,
                notes=f"Long Relief: {lr.stamina} stamina",
            ))

        # Fill remaining bullpen
        remaining = [p for p in bp_candidates if p.name not in used]
        for i, pitcher in enumerate(remaining[:3]):
            used.add(pitcher.name)
            role = PitcherRole.MATCHUP_LEFTY if pitcher.throws == "L" else PitcherRole.MIDDLE_RELIEF
            bullpen.append(RotationSlot(
                card=pitcher,
                role=role,
                order=len(bullpen) + 1,
                notes=f"{role.value}: {pitcher.overall} OVR",
            ))

        return DDPitchingStaff(
            rotation=starters,
            bullpen=bullpen,
        )

    # ------------------------------------------------------------------
    # Staff analysis
    # ------------------------------------------------------------------

    def analyze_staff(
        self,
        staff: DDPitchingStaff,
    ) -> StaffAnalysis:
        """Analyze a pitching staff for strengths, weaknesses, and meta fit."""
        all_pitchers = staff.rotation + staff.bullpen
        avg_velo = sum(s.card.velocity for s in all_pitchers) / max(len(all_pitchers), 1)
        avg_ovr = sum(s.card.overall for s in all_pitchers) / max(len(all_pitchers), 1)

        strengths: list[str] = []
        weaknesses: list[str] = []

        # Rotation depth
        if len(staff.rotation) >= 5:
            strengths.append("Full 5-man rotation — no fatigue concerns.")
        else:
            weaknesses.append(f"Only {len(staff.rotation)} starters — need more rotation depth.")

        # Closer quality
        closers = [p for p in staff.bullpen if p.role == PitcherRole.CLOSER]
        if closers and closers[0].card.overall >= 95:
            strengths.append("Elite closer — lock down the 9th inning.")
        elif not closers:
            weaknesses.append("No designated closer — consider acquiring one.")

        # Bullpen depth
        if len(staff.bullpen) < 5:
            weaknesses.append("Thin bullpen — need more arms for extra-inning games.")

        # Velocity assessment
        if avg_velo >= 95:
            strengths.append("Power pitching staff — velocity plays at higher levels.")
        elif avg_velo < 90:
            weaknesses.append("Low velocity — rely on movement and control.")

        # Lefty representation
        lefties = sum(1 for p in all_pitchers if p.card.throws == "L")
        if lefties == 0:
            weaknesses.append("No lefty pitchers — vulnerable to LHH stacking.")
        elif lefties >= 3:
            strengths.append("Good lefty representation for platoon advantages.")

        return StaffAnalysis(
            rotation_avg_ovr=round(sum(s.card.overall for s in staff.rotation) / max(len(staff.rotation), 1), 1),
            bullpen_avg_ovr=round(sum(s.card.overall for s in staff.bullpen) / max(len(staff.bullpen), 1), 1),
            avg_velocity=round(avg_velo, 1),
            strengths=strengths,
            weaknesses=weaknesses,
            overall_grade=self._grade_staff(avg_ovr, len(staff.rotation), len(staff.bullpen)),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _score_for_slot(
        card: DDPlayerCard,
        rules: dict[str, Any],
        platoon: str,
    ) -> float:
        score = card.overall * 0.01
        priorities = rules.get("priority", [])
        for i, attr in enumerate(priorities):
            weight = 1.0 - (i * 0.2)
            val = getattr(card, attr, 0) or 0
            score += val * 0.01 * weight

        # Platoon bonus
        if platoon == "vs_rhp" and card.bats in ("L", "S"):
            score += 0.15
        elif platoon == "vs_lhp" and card.bats in ("R", "S"):
            score += 0.15

        return score

    @staticmethod
    def _grade_staff(avg_ovr: float, sp_count: int, bp_count: int) -> str:
        if avg_ovr >= 95 and sp_count >= 5 and bp_count >= 5:
            return "A+"
        if avg_ovr >= 92 and sp_count >= 5:
            return "A"
        if avg_ovr >= 88:
            return "B+"
        if avg_ovr >= 85:
            return "B"
        return "C"


# Module-level singleton
diamond_dynasty_iq = DiamondDynastyIQ()

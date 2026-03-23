"""SquadOps AI — role assignment, callout efficiency tracker, revive priority decision engine.

Provides squad-level intelligence for Warzone by analyzing player profiles,
assigning optimal roles, evaluating communication, and prioritizing revives.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.warzone.combat import (
    EngagementRange,
    RevivePriority,
    RoleAssignment,
    SquadAnalysis,
    SquadMember,
    SquadOpsRequest,
    SquadRole,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Role scoring weights
# ---------------------------------------------------------------------------

# Each role has weighted criteria: (stat_name, weight, threshold_for_bonus)
_ROLE_CRITERIA: dict[SquadRole, list[tuple[str, float, float]]] = {
    SquadRole.IGL: [
        ("win_rate", 0.35, 0.15),
        ("comms_score", 0.35, 0.7),
        ("kd_ratio", 0.15, 1.5),
        ("avg_damage", 0.15, 800),
    ],
    SquadRole.FRAGGER: [
        ("kd_ratio", 0.35, 2.0),
        ("avg_damage", 0.30, 1200),
        ("clutch_rate", 0.20, 0.3),
        ("comms_score", 0.15, 0.5),
    ],
    SquadRole.SUPPORT: [
        ("comms_score", 0.30, 0.7),
        ("win_rate", 0.30, 0.12),
        ("avg_damage", 0.20, 600),
        ("kd_ratio", 0.20, 1.0),
    ],
    SquadRole.SNIPER: [
        ("kd_ratio", 0.30, 2.0),
        ("avg_damage", 0.25, 900),
        ("clutch_rate", 0.25, 0.25),
        ("comms_score", 0.20, 0.6),
    ],
    SquadRole.FLEX: [
        ("kd_ratio", 0.25, 1.5),
        ("avg_damage", 0.25, 800),
        ("win_rate", 0.25, 0.12),
        ("comms_score", 0.25, 0.6),
    ],
}

# Loadout style recommendations per role
_ROLE_LOADOUT_STYLE: dict[SquadRole, str] = {
    SquadRole.IGL: "Balanced AR + SMG — needs to fight at any range while leading rotations",
    SquadRole.FRAGGER: "Aggressive SMG primary — optimized for entry kills and fast TTK",
    SquadRole.SUPPORT: "Versatile AR + utility — focus on trades and buyback economy",
    SquadRole.SNIPER: "Sniper + SMG overkill — long-range picks into CQB swap",
    SquadRole.FLEX: "Adaptive loadout — swaps based on zone and team needs",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _score_player_for_role(player: SquadMember, role: SquadRole) -> float:
    """Score how well a player fits a given role (0-100)."""
    criteria = _ROLE_CRITERIA.get(role, _ROLE_CRITERIA[SquadRole.FLEX])
    total = 0.0

    for stat_name, weight, threshold in criteria:
        val = getattr(player, stat_name, 0.0)
        # Normalize: value / threshold gives a ratio; cap at 1.5 to prevent outlier dominance
        normalized = min(1.5, val / max(threshold, 0.001))
        total += normalized * weight * 100

    # Range preference bonus for SNIPER role
    if role == SquadRole.SNIPER and player.preferred_range in (EngagementRange.LONG, EngagementRange.EXTREME):
        total += 10
    elif role == SquadRole.FRAGGER and player.preferred_range in (EngagementRange.CQB, EngagementRange.SHORT):
        total += 10

    return round(min(100.0, total), 1)


def _generate_role_reasoning(player: SquadMember, role: SquadRole, score: float) -> str:
    """Generate a human-readable explanation for a role assignment."""
    parts = [f"{player.gamertag} scored {score:.0f}/100 for {role.value}."]

    if role == SquadRole.IGL:
        parts.append(
            f"Win rate ({player.win_rate:.0%}) and comms ({player.comms_score:.0%}) "
            f"make them the best shot-caller."
        )
    elif role == SquadRole.FRAGGER:
        parts.append(
            f"K/D ({player.kd_ratio:.2f}) and avg damage ({player.avg_damage:.0f}) "
            f"indicate strong slaying potential."
        )
    elif role == SquadRole.SUPPORT:
        parts.append(
            f"Solid comms ({player.comms_score:.0%}) and consistent performance "
            f"make them ideal for utility and trade support."
        )
    elif role == SquadRole.SNIPER:
        parts.append(
            f"Long-range preference and K/D ({player.kd_ratio:.2f}) "
            f"suit a dedicated sniper role."
        )
    else:
        parts.append(
            f"Well-rounded stats allow them to flex across roles as needed."
        )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# SquadOps
# ---------------------------------------------------------------------------

class SquadOps:
    """Squad operations intelligence — roles, comms, revive priority."""

    # ------------------------------------------------------------------
    # assign_roles
    # ------------------------------------------------------------------

    def assign_roles(self, squad: list[SquadMember]) -> list[RoleAssignment]:
        """Assign optimal roles to each squad member.

        Uses a greedy assignment: score every player for every role,
        then assign the best-fit player to each role without duplication.
        """
        if not squad:
            return []

        # Score matrix: {player_id: {role: score}}
        score_matrix: dict[str, dict[SquadRole, float]] = {}
        for player in squad:
            score_matrix[player.player_id] = {
                role: _score_player_for_role(player, role)
                for role in SquadRole
            }

        # Greedy assignment
        assigned: dict[str, SquadRole] = {}
        taken_roles: set[SquadRole] = set()
        player_map = {p.player_id: p for p in squad}

        # Priority roles to fill first
        role_priority = [SquadRole.IGL, SquadRole.FRAGGER, SquadRole.SNIPER, SquadRole.SUPPORT, SquadRole.FLEX]

        for role in role_priority:
            if role in taken_roles:
                continue
            best_pid = None
            best_score = -1.0
            for pid, scores in score_matrix.items():
                if pid in assigned:
                    continue
                if scores[role] > best_score:
                    best_score = scores[role]
                    best_pid = pid

            if best_pid:
                assigned[best_pid] = role
                taken_roles.add(role)

            if len(assigned) >= len(squad):
                break

        # Assign remaining players to FLEX
        for player in squad:
            if player.player_id not in assigned:
                assigned[player.player_id] = SquadRole.FLEX

        # Build response
        assignments: list[RoleAssignment] = []
        for pid, role in assigned.items():
            player = player_map[pid]
            score = score_matrix[pid][role]
            assignments.append(RoleAssignment(
                player_id=pid,
                gamertag=player.gamertag,
                assigned_role=role,
                confidence=round(min(1.0, score / 100), 2),
                reasoning=_generate_role_reasoning(player, role, score),
                recommended_loadout_style=_ROLE_LOADOUT_STYLE.get(role, "Balanced"),
            ))

        return sorted(assignments, key=lambda a: a.confidence, reverse=True)

    # ------------------------------------------------------------------
    # calculate_callout_efficiency
    # ------------------------------------------------------------------

    def calculate_callout_efficiency(self, squad: list[SquadMember]) -> float:
        """Evaluate squad communication efficiency based on individual comms scores.

        Returns a 0-1 score where 1.0 means perfect comms synergy.
        """
        if not squad:
            return 0.0

        avg_comms = sum(m.comms_score for m in squad) / len(squad)

        # Variance penalty: inconsistent comms hurt more than low-but-consistent
        if len(squad) > 1:
            variance = sum((m.comms_score - avg_comms) ** 2 for m in squad) / len(squad)
            consistency_bonus = max(0.0, 0.1 - variance)
        else:
            consistency_bonus = 0.05

        return round(min(1.0, avg_comms + consistency_bonus), 2)

    # ------------------------------------------------------------------
    # decide_revive_priority
    # ------------------------------------------------------------------

    def decide_revive_priority(
        self,
        downed_players: list[SquadMember],
        context: str = "mid-game",
    ) -> RevivePriority:
        """Determine revive order when multiple teammates are down.

        Factors: role importance, K/D contribution, clutch potential,
        and game context.
        """
        if not downed_players:
            return RevivePriority(
                priority_order=[],
                reasoning=["No downed players."],
                context=context,
            )

        # Score each downed player for revive priority
        scored: list[tuple[float, SquadMember, str]] = []

        for player in downed_players:
            score = 0.0
            reasons: list[str] = []

            # KD contribution
            kd_score = min(30.0, player.kd_ratio * 10)
            score += kd_score

            # Damage output
            dmg_score = min(25.0, player.avg_damage / 50)
            score += dmg_score

            # Clutch ability (especially important in late game)
            if "late" in context.lower() or "final" in context.lower():
                clutch_score = player.clutch_rate * 30
                reasons.append(f"Clutch rate ({player.clutch_rate:.0%}) critical in {context}")
            else:
                clutch_score = player.clutch_rate * 15
            score += clutch_score

            # Comms — IGL-type players are high priority
            if player.comms_score > 0.7:
                score += 15
                reasons.append(f"High comms ({player.comms_score:.0%}) — likely IGL")

            if not reasons:
                reasons.append(
                    f"K/D {player.kd_ratio:.2f}, avg damage {player.avg_damage:.0f}"
                )

            scored.append((score, player, "; ".join(reasons)))

        scored.sort(key=lambda x: x[0], reverse=True)

        return RevivePriority(
            priority_order=[s[1].player_id for s in scored],
            reasoning=[s[2] for s in scored],
            context=context,
        )

    # ------------------------------------------------------------------
    # analyze_squad (full pipeline)
    # ------------------------------------------------------------------

    def analyze_squad(self, request: SquadOpsRequest) -> SquadAnalysis:
        """Full squad operations analysis — roles, comms, revive, synergy."""
        squad = request.squad

        roles = self.assign_roles(squad)
        comms_eff = self.calculate_callout_efficiency(squad)
        revive = self.decide_revive_priority(squad, request.match_context or "mid-game")

        # Squad synergy: based on role coverage and stat balance
        role_set = {r.assigned_role for r in roles}
        role_coverage = len(role_set) / min(len(SquadRole), max(len(squad), 1))

        avg_kd = sum(m.kd_ratio for m in squad) / max(len(squad), 1)
        avg_wr = sum(m.win_rate for m in squad) / max(len(squad), 1)

        synergy = min(100.0, (
            role_coverage * 30 +
            comms_eff * 30 +
            min(1.0, avg_kd / 2.0) * 20 +
            min(1.0, avg_wr / 0.15) * 20
        ))

        # Improvement tips
        tips: list[str] = []
        if comms_eff < 0.6:
            tips.append("Squad comms are below average — run callout drills in practice matches.")
        if avg_kd < 1.0:
            tips.append("Overall K/D is below 1.0 — focus on gunfight training and positioning.")
        if role_coverage < 0.6:
            tips.append("Role diversity is low — consider diversifying loadouts and playstyles.")
        if not any(r.assigned_role == SquadRole.IGL for r in roles):
            tips.append("No clear IGL — designate a shot-caller for rotation and engagement calls.")
        if not tips:
            tips.append("Squad is performing well — maintain consistency and focus on late-game execution.")

        igl = next((r for r in roles if r.assigned_role == SquadRole.IGL), None)
        igl_name = igl.gamertag if igl else "Unassigned"

        summary = (
            f"Squad synergy: {synergy:.0f}/100. IGL: {igl_name}. "
            f"Comms efficiency: {comms_eff:.0%}. "
            f"Average K/D: {avg_kd:.2f}. "
            f"{len(tips)} improvement area(s) identified."
        )

        return SquadAnalysis(
            role_assignments=roles,
            revive_priority=revive,
            callout_efficiency=comms_eff,
            squad_synergy_score=round(synergy, 1),
            improvement_tips=tips,
            summary=summary,
        )

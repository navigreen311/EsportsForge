"""DribbleForge — dribble combo mastery, isolation counter library, pro efficiency comparison.

Teaches NBA 2K26 dribble move chains, tracks mastery of combos, provides counter moves
against specific defensive tendencies, and compares user efficiency to pro players.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from app.schemas.nba2k26.gameplay import (
    DribbleCombo,
    DribbleMastery,
    DribbleMove,
    DribbleMoveType,
    IsolationCounter,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dribble combo library — proven effective chains
# ---------------------------------------------------------------------------

COMBO_LIBRARY: list[DribbleCombo] = [
    DribbleCombo(
        name="Hesi-Cross-Stepback",
        moves=[
            DribbleMove(move_type=DribbleMoveType.HESITATION, direction="forward"),
            DribbleMove(move_type=DribbleMoveType.CROSSOVER, direction="left"),
            DribbleMove(move_type=DribbleMoveType.STEPBACK, direction="right"),
        ],
        difficulty=0.6,
        effectiveness=0.78,
        best_against=["aggressive on-ball", "reaches for steals"],
        min_ball_handle=80,
    ),
    DribbleCombo(
        name="Size-Up Spin-Finish",
        moves=[
            DribbleMove(move_type=DribbleMoveType.SIZE_UP, direction="forward"),
            DribbleMove(move_type=DribbleMoveType.SPIN_MOVE, direction="left"),
        ],
        difficulty=0.5,
        effectiveness=0.72,
        best_against=["sags off", "plays the passing lane"],
        min_ball_handle=75,
    ),
    DribbleCombo(
        name="BTL-Snatch-Hesi",
        moves=[
            DribbleMove(move_type=DribbleMoveType.BETWEEN_LEGS, direction="right"),
            DribbleMove(move_type=DribbleMoveType.SNATCH_BACK, direction="left"),
            DribbleMove(move_type=DribbleMoveType.HESITATION, direction="forward"),
        ],
        difficulty=0.75,
        effectiveness=0.85,
        best_against=["aggressive on-ball", "jumps at fakes"],
        min_ball_handle=85,
    ),
    DribbleCombo(
        name="Cross-Behind-Pull",
        moves=[
            DribbleMove(move_type=DribbleMoveType.CROSSOVER, direction="left"),
            DribbleMove(move_type=DribbleMoveType.BEHIND_BACK, direction="right"),
            DribbleMove(move_type=DribbleMoveType.STEPBACK, direction="left"),
        ],
        difficulty=0.7,
        effectiveness=0.80,
        best_against=["plays tight", "anticipates first move"],
        min_ball_handle=82,
    ),
    DribbleCombo(
        name="Escape-Cross-Drive",
        moves=[
            DribbleMove(move_type=DribbleMoveType.ESCAPE_DRIBBLE, direction="right"),
            DribbleMove(move_type=DribbleMoveType.CROSSOVER, direction="left"),
        ],
        difficulty=0.4,
        effectiveness=0.68,
        best_against=["trapping defense", "double teams"],
        min_ball_handle=70,
    ),
    DribbleCombo(
        name="In-Out-Spin-Finish",
        moves=[
            DribbleMove(move_type=DribbleMoveType.IN_AND_OUT, direction="right"),
            DribbleMove(move_type=DribbleMoveType.SPIN_MOVE, direction="left"),
        ],
        difficulty=0.55,
        effectiveness=0.74,
        best_against=["bites on fakes", "slow lateral movement"],
        min_ball_handle=78,
    ),
    DribbleCombo(
        name="Triple-Hesi Chain",
        moves=[
            DribbleMove(move_type=DribbleMoveType.HESITATION, direction="forward"),
            DribbleMove(move_type=DribbleMoveType.HESITATION, direction="forward"),
            DribbleMove(move_type=DribbleMoveType.CROSSOVER, direction="left"),
        ],
        difficulty=0.45,
        effectiveness=0.70,
        best_against=["patient defenders", "zone defense"],
        min_ball_handle=75,
    ),
    DribbleCombo(
        name="Snatch-BTL-Stepback-Three",
        moves=[
            DribbleMove(move_type=DribbleMoveType.SNATCH_BACK, direction="left"),
            DribbleMove(move_type=DribbleMoveType.BETWEEN_LEGS, direction="right"),
            DribbleMove(move_type=DribbleMoveType.STEPBACK, direction="left"),
        ],
        difficulty=0.85,
        effectiveness=0.88,
        best_against=["any on-ball defense", "switches"],
        min_ball_handle=90,
    ),
]

# ---------------------------------------------------------------------------
# Isolation counter database
# ---------------------------------------------------------------------------

ISOLATION_COUNTERS: dict[str, list[IsolationCounter]] = {
    "reaches": [
        IsolationCounter(
            defender_tendency="reaches",
            counter_combo=COMBO_LIBRARY[0],  # Hesi-Cross-Stepback
            success_rate=0.82,
            explanation="The hesitation baits the reach, crossover exploits the off-balance recovery.",
        ),
        IsolationCounter(
            defender_tendency="reaches",
            counter_combo=COMBO_LIBRARY[2],  # BTL-Snatch-Hesi
            success_rate=0.78,
            explanation="Between-the-legs keeps the ball protected from the reach attempt.",
        ),
    ],
    "sags_off": [
        IsolationCounter(
            defender_tendency="sags_off",
            counter_combo=COMBO_LIBRARY[1],  # Size-Up Spin-Finish
            success_rate=0.75,
            explanation="Size-up closes the gap, spin move blows by the flat-footed defender.",
        ),
    ],
    "plays_tight": [
        IsolationCounter(
            defender_tendency="plays_tight",
            counter_combo=COMBO_LIBRARY[3],  # Cross-Behind-Pull
            success_rate=0.80,
            explanation="Quick directional changes freeze the tight defender and create space.",
        ),
    ],
    "jumps_at_fakes": [
        IsolationCounter(
            defender_tendency="jumps_at_fakes",
            counter_combo=COMBO_LIBRARY[6],  # Triple-Hesi Chain
            success_rate=0.85,
            explanation="Chain hesitations exploit the defender's tendency to bite on every fake.",
        ),
    ],
    "anticipates_moves": [
        IsolationCounter(
            defender_tendency="anticipates_moves",
            counter_combo=COMBO_LIBRARY[7],  # Snatch-BTL-Stepback
            success_rate=0.76,
            explanation="Complex chain is too many reads for an anticipating defender to predict.",
        ),
    ],
}

# ---------------------------------------------------------------------------
# Pro player efficiency benchmarks
# ---------------------------------------------------------------------------

PRO_BENCHMARKS: dict[str, dict] = {
    "Kyrie Irving": {
        "iso_win_rate": 0.72,
        "avg_separation_ft": 4.2,
        "signature_moves": [DribbleMoveType.CROSSOVER, DribbleMoveType.SPIN_MOVE],
        "style": "Creative finisher with elite handle",
    },
    "Luka Doncic": {
        "iso_win_rate": 0.68,
        "avg_separation_ft": 3.8,
        "signature_moves": [DribbleMoveType.STEPBACK, DribbleMoveType.HESITATION],
        "style": "Methodical iso scorer with stepback three",
    },
    "James Harden": {
        "iso_win_rate": 0.70,
        "avg_separation_ft": 4.5,
        "signature_moves": [DribbleMoveType.STEPBACK, DribbleMoveType.CROSSOVER],
        "style": "Stepback specialist with elite deceleration",
    },
    "Jamal Crawford": {
        "iso_win_rate": 0.65,
        "avg_separation_ft": 3.5,
        "signature_moves": [DribbleMoveType.BEHIND_BACK, DribbleMoveType.BETWEEN_LEGS],
        "style": "Flashy ball handler with shake-and-bake moves",
    },
    "Chris Paul": {
        "iso_win_rate": 0.64,
        "avg_separation_ft": 3.2,
        "signature_moves": [DribbleMoveType.HESITATION, DribbleMoveType.IN_AND_OUT],
        "style": "Controlled, efficient point guard with crafty moves",
    },
    "Allen Iverson": {
        "iso_win_rate": 0.71,
        "avg_separation_ft": 4.8,
        "signature_moves": [DribbleMoveType.CROSSOVER, DribbleMoveType.HESITATION],
        "style": "Explosive crossover king, all-time iso legend",
    },
}


class DribbleForge:
    """NBA 2K26 dribble mastery engine.

    Tracks user's dribble combo mastery, recommends counters for specific
    defensive tendencies, and benchmarks performance against pro standards.
    """

    def __init__(self) -> None:
        self._user_mastery: dict[str, DribbleMastery] = {}
        self._user_iso_results: dict[str, list[dict]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Combo library access
    # ------------------------------------------------------------------

    def get_combos(
        self,
        min_ball_handle: int = 25,
        max_difficulty: float = 1.0,
    ) -> list[DribbleCombo]:
        """Get available dribble combos filtered by ball handle and difficulty.

        Returns combos the user can execute based on their ball handle attribute.
        """
        return [
            combo for combo in COMBO_LIBRARY
            if combo.min_ball_handle <= min_ball_handle
            and combo.difficulty <= max_difficulty
        ]

    def get_combo_by_name(self, name: str) -> DribbleCombo | None:
        """Look up a specific combo by name."""
        for combo in COMBO_LIBRARY:
            if combo.name.lower() == name.lower():
                return combo
        return None

    # ------------------------------------------------------------------
    # Isolation counter library
    # ------------------------------------------------------------------

    def get_isolation_counters(self, defender_tendency: str) -> list[IsolationCounter]:
        """Get counter combos for a specific defensive tendency.

        Maps common defender behaviors to the most effective dribble chains.
        """
        # Normalize the tendency key
        key = defender_tendency.lower().replace(" ", "_").replace("-", "_")
        counters = ISOLATION_COUNTERS.get(key, [])

        if not counters:
            # Return generic counters
            return [
                IsolationCounter(
                    defender_tendency=defender_tendency,
                    counter_combo=COMBO_LIBRARY[0],
                    success_rate=0.60,
                    explanation="Default counter — hesi-cross-stepback works against most defenders.",
                ),
            ]

        return counters

    # ------------------------------------------------------------------
    # Mastery tracking
    # ------------------------------------------------------------------

    def record_iso_attempt(
        self,
        user_id: str,
        combo_name: str,
        success: bool,
        separation_ft: float = 0.0,
    ) -> DribbleMastery:
        """Record an isolation attempt and update mastery profile.

        Tracks success rate, separation created, and combo execution.
        """
        self._user_iso_results[user_id].append({
            "combo": combo_name,
            "success": success,
            "separation_ft": separation_ft,
        })

        results = self._user_iso_results[user_id]
        total = len(results)
        wins = sum(1 for r in results if r["success"])
        iso_win_rate = wins / max(total, 1)
        avg_sep = sum(r["separation_ft"] for r in results) / max(total, 1)

        # Determine most/least effective moves
        move_success: dict[str, list[bool]] = defaultdict(list)
        for r in results:
            move_success[r["combo"]].append(r["success"])

        best_combo = max(
            move_success.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
            default=("", []),
        )
        worst_combo = min(
            move_success.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
            default=("", []),
        )

        # Map combo names to move types for most/weakest
        most_effective = None
        weakest = None
        best_found = self.get_combo_by_name(best_combo[0])
        worst_found = self.get_combo_by_name(worst_combo[0])
        if best_found and best_found.moves:
            most_effective = best_found.moves[0].move_type
        if worst_found and worst_found.moves:
            weakest = worst_found.moves[0].move_type

        # Pro comparison
        pro_comp = self._find_pro_comparison(iso_win_rate, avg_sep)

        # Mastered combos (70%+ win rate with 5+ attempts)
        mastered: list[DribbleCombo] = []
        for combo_name_key, successes in move_success.items():
            if len(successes) >= 5 and sum(successes) / len(successes) >= 0.7:
                found = self.get_combo_by_name(combo_name_key)
                if found:
                    mastered.append(found)

        mastery = DribbleMastery(
            user_id=user_id,
            combos_mastered=mastered,
            isolation_win_rate=round(iso_win_rate, 3),
            avg_separation_created_ft=round(avg_sep, 2),
            most_effective_move=most_effective,
            weakest_move=weakest,
            pro_comparison=pro_comp,
        )

        self._user_mastery[user_id] = mastery

        logger.info(
            "Iso attempt recorded: user=%s combo=%s success=%s iso_wr=%.1f%%",
            user_id, combo_name, success, iso_win_rate * 100,
        )
        return mastery

    def get_mastery(self, user_id: str) -> DribbleMastery:
        """Get current dribble mastery profile for a user."""
        if user_id in self._user_mastery:
            return self._user_mastery[user_id]
        return DribbleMastery(user_id=user_id)

    # ------------------------------------------------------------------
    # Pro efficiency comparison
    # ------------------------------------------------------------------

    def _find_pro_comparison(self, iso_win_rate: float, avg_sep: float) -> str:
        """Find the closest pro comparison based on iso efficiency."""
        best_match = ""
        best_diff = float("inf")

        for name, stats in PRO_BENCHMARKS.items():
            diff = abs(stats["iso_win_rate"] - iso_win_rate) + abs(stats["avg_separation_ft"] - avg_sep) * 0.1
            if diff < best_diff:
                best_diff = diff
                best_match = name

        return best_match

    def compare_to_pro(self, user_id: str, pro_name: str) -> dict:
        """Compare a user's dribble stats to a specific pro player.

        Returns a detailed comparison with the pro's stats and the user's stats.
        """
        mastery = self.get_mastery(user_id)
        pro = PRO_BENCHMARKS.get(pro_name)

        if not pro:
            return {"error": f"Unknown pro player: {pro_name}"}

        return {
            "user_id": user_id,
            "pro_name": pro_name,
            "pro_style": pro["style"],
            "iso_win_rate_diff": round(mastery.isolation_win_rate - pro["iso_win_rate"], 3),
            "separation_diff_ft": round(
                mastery.avg_separation_created_ft - pro["avg_separation_ft"], 2,
            ),
            "user_iso_win_rate": mastery.isolation_win_rate,
            "pro_iso_win_rate": pro["iso_win_rate"],
            "user_avg_separation": mastery.avg_separation_created_ft,
            "pro_avg_separation": pro["avg_separation_ft"],
            "pro_signature_moves": [m.value for m in pro["signature_moves"]],
            "areas_to_improve": self._suggest_improvements(mastery, pro),
        }

    def _suggest_improvements(self, mastery: DribbleMastery, pro: dict) -> list[str]:
        """Suggest improvements to match pro level."""
        suggestions: list[str] = []

        if mastery.isolation_win_rate < pro["iso_win_rate"]:
            gap = pro["iso_win_rate"] - mastery.isolation_win_rate
            suggestions.append(
                f"Improve iso win rate by {gap:.0%} — practice reading the defender first"
            )

        if mastery.avg_separation_created_ft < pro["avg_separation_ft"]:
            suggestions.append(
                "Create more separation — focus on explosive first step after dribble moves"
            )

        if not mastery.combos_mastered:
            suggestions.append("Master at least 3 combos before focusing on pro-level metrics")

        if not suggestions:
            suggestions.append("Performing at pro level — maintain consistency in competitive play")

        return suggestions


# Module-level singleton
dribble_forge = DribbleForge()

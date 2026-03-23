"""FormationRecognition — identify formations, coverage shells, and suggest counters.

Uses visual analysis data to detect offensive formations and defensive
coverage shells, then suggests optimal counters.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.visionaudio import (
    CoverageShell,
    FormationDetection,
    FormationCounter,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Formation recognition rules
# ---------------------------------------------------------------------------

_OFFENSIVE_FORMATIONS: dict[str, dict[str, Any]] = {
    "shotgun_spread": {
        "player_positions": {"qb": "shotgun", "rb": "beside_qb", "wr": 3, "te": 0},
        "indicators": ["5_wide_split", "empty_box", "no_te_on_line"],
        "strengths": ["Quick passing", "Spread defense", "Screen game"],
        "weaknesses": ["Run blocking", "Protection in max blitz"],
    },
    "singleback": {
        "player_positions": {"qb": "under_center", "rb": "i_back", "wr": 2, "te": 1},
        "indicators": ["tight_alignment", "te_on_line", "balanced_look"],
        "strengths": ["Run game", "Play action", "Balanced attack"],
        "weaknesses": ["Predictable in short yardage", "Slow developing plays"],
    },
    "pistol": {
        "player_positions": {"qb": "pistol", "rb": "behind_qb", "wr": 2, "te": 1},
        "indicators": ["qb_pistol_depth", "rb_directly_behind"],
        "strengths": ["RPO", "Read option", "Quick run game"],
        "weaknesses": ["Deep passing", "Max protection"],
    },
    "gun_bunch": {
        "player_positions": {"qb": "shotgun", "rb": "beside_qb", "wr": 3, "te": 1},
        "indicators": ["3_wr_bunched", "tight_splits"],
        "strengths": ["Route combinations", "Natural picks", "Short-area passing"],
        "weaknesses": ["No width", "Vulnerable to zone flooding"],
    },
    "i_formation": {
        "player_positions": {"qb": "under_center", "fb": "ahead_of_rb", "rb": "deep_i", "te": 1},
        "indicators": ["two_backs_aligned", "fullback_lead"],
        "strengths": ["Power run", "Play action", "Goal line"],
        "weaknesses": ["Speed", "Spread passing"],
    },
}

_COVERAGE_SHELLS: dict[str, dict[str, Any]] = {
    "cover_0": {"safeties_deep": 0, "corners": "press", "description": "All-out man coverage, no safety help"},
    "cover_1": {"safeties_deep": 1, "corners": "press_or_off", "description": "Single high safety, man underneath"},
    "cover_2": {"safeties_deep": 2, "corners": "flat_zone", "description": "Two deep safeties, flat coverage"},
    "cover_3": {"safeties_deep": 1, "corners": "deep_third", "description": "Three deep zones, four underneath"},
    "cover_4": {"safeties_deep": 2, "corners": "deep_quarter", "description": "Four deep quarters coverage"},
    "cover_6": {"safeties_deep": 2, "corners": "mixed", "description": "Split coverage — Cover 2 one side, Cover 4 other"},
}

_FORMATION_COUNTERS: dict[str, FormationCounter] = {
    "shotgun_spread": FormationCounter(
        formation="shotgun_spread",
        counter_defense="Nickel / Dime — match personnel",
        adjustments=["Play Cover 3 or Cover 4 to match wide receivers", "Send zone blitzes to confuse the QB"],
        key="Get pressure with 4 — dont blitz into empty formations",
    ),
    "gun_bunch": FormationCounter(
        formation="gun_bunch",
        counter_defense="Cover 3 Match — deny the bunch concepts",
        adjustments=["Switch to zone coverage to avoid rub routes", "User the middle linebacker over the bunch"],
        key="Dont play man coverage — the natural picks will beat you",
    ),
    "i_formation": FormationCounter(
        formation="i_formation",
        counter_defense="4-4 / Bear front — stack the box",
        adjustments=["Bring a safety into the box", "Pinch the defensive line"],
        key="Force them to throw — take away the run game",
    ),
    "pistol": FormationCounter(
        formation="pistol",
        counter_defense="3-4 Odd — option assignment discipline",
        adjustments=["Assign the DE to the QB on read option", "Spy the QB with a linebacker"],
        key="Discipline on the read — dont get optioned",
    ),
}


class FormationRecognition:
    """Visual formation recognition and counter-suggestion engine.

    Identifies offensive formations and defensive coverage shells from
    player position data and suggests optimal counters.
    """

    # ------------------------------------------------------------------
    # Identify formation
    # ------------------------------------------------------------------

    def identify_formation(
        self,
        player_positions: list[dict[str, Any]],
    ) -> FormationDetection:
        """Identify the offensive formation from detected player positions.

        Each player_positions entry should have: x, y, role (qb/rb/wr/te/ol), team.
        """
        if not player_positions:
            return FormationDetection(
                formation="unknown", confidence=0.0, indicators=[],
                strengths=[], weaknesses=[],
            )

        # Count offensive personnel
        offense = [p for p in player_positions if p.get("team") == "offense"]
        wr_count = sum(1 for p in offense if p.get("role") == "wr")
        te_count = sum(1 for p in offense if p.get("role") == "te")
        rb_count = sum(1 for p in offense if p.get("role") in ("rb", "fb"))
        qb = next((p for p in offense if p.get("role") == "qb"), None)

        # QB depth classification
        qb_depth = "unknown"
        if qb:
            y = qb.get("y", 0)
            if y > 7:
                qb_depth = "shotgun"
            elif y > 4:
                qb_depth = "pistol"
            else:
                qb_depth = "under_center"

        # Match against known formations
        best_match = "unknown"
        best_score = 0
        best_data: dict[str, Any] = {}

        for name, data in _OFFENSIVE_FORMATIONS.items():
            score = 0
            positions = data["player_positions"]

            if positions.get("qb") == qb_depth:
                score += 3
            if positions.get("wr") == wr_count:
                score += 2
            if positions.get("te", -1) == te_count:
                score += 1

            if score > best_score:
                best_score = score
                best_match = name
                best_data = data

        confidence = min(0.95, best_score / 6.0)

        return FormationDetection(
            formation=best_match,
            confidence=round(confidence, 3),
            indicators=best_data.get("indicators", []),
            strengths=best_data.get("strengths", []),
            weaknesses=best_data.get("weaknesses", []),
            personnel=f"{rb_count}RB {te_count}TE {wr_count}WR",
        )

    # ------------------------------------------------------------------
    # Identify coverage shell
    # ------------------------------------------------------------------

    def identify_coverage_shell(
        self,
        defender_positions: list[dict[str, Any]],
    ) -> CoverageShell:
        """Identify the defensive coverage shell from defender positions.

        Each entry: x, y, role (cb/ss/fs/lb/dl), depth.
        """
        if not defender_positions:
            return CoverageShell(
                coverage="unknown", confidence=0.0, description="No data.",
                vulnerable_zones=[], recommended_attacks=[],
            )

        safeties = [d for d in defender_positions if d.get("role") in ("ss", "fs")]
        deep_safeties = sum(1 for s in safeties if s.get("depth", 0) > 12)
        corners = [d for d in defender_positions if d.get("role") == "cb"]
        press_corners = sum(1 for c in corners if c.get("depth", 5) < 3)

        # Match coverage shell
        if deep_safeties == 0 and press_corners >= 2:
            coverage = "cover_0"
        elif deep_safeties == 1 and press_corners >= 1:
            coverage = "cover_1"
        elif deep_safeties == 2 and press_corners == 0:
            coverage = "cover_2"
        elif deep_safeties == 1 and press_corners == 0:
            coverage = "cover_3"
        elif deep_safeties == 2:
            coverage = "cover_4"
        else:
            coverage = "cover_3"

        shell_data = _COVERAGE_SHELLS.get(coverage, {})

        # Vulnerable zones and attack recommendations
        vuln_map: dict[str, list[str]] = {
            "cover_0": ["Deep middle", "Deep sideline"],
            "cover_1": ["Deep sideline opposite safety", "Seam routes"],
            "cover_2": ["Deep middle hole shot", "Sideline between flat and deep half"],
            "cover_3": ["Flat zones", "Curl windows", "Seam between deep thirds"],
            "cover_4": ["Underneath hooks and curls", "Drag routes"],
            "cover_6": ["Cover-2 side deep middle", "Cover-4 side underneath"],
        }
        attack_map: dict[str, list[str]] = {
            "cover_0": ["Quick slants", "Go routes — no safety help"],
            "cover_1": ["Post route", "Corner route away from safety"],
            "cover_2": ["Four verticals", "TE seam up the middle"],
            "cover_3": ["Flood concept", "Curl/flat combos"],
            "cover_4": ["Mesh/drive concepts", "HB checkdowns"],
            "cover_6": ["Smash to Cover-2 side", "Underneath to Cover-4 side"],
        }

        return CoverageShell(
            coverage=coverage,
            confidence=round(min(0.90, 0.6 + deep_safeties * 0.1 + press_corners * 0.05), 3),
            description=shell_data.get("description", "Unknown coverage shell"),
            vulnerable_zones=vuln_map.get(coverage, []),
            recommended_attacks=attack_map.get(coverage, []),
        )

    # ------------------------------------------------------------------
    # Suggest counter
    # ------------------------------------------------------------------

    def suggest_counter(
        self,
        formation: str,
    ) -> FormationCounter:
        """Suggest a defensive counter for the identified offensive formation."""
        counter = _FORMATION_COUNTERS.get(formation)
        if counter:
            return counter

        return FormationCounter(
            formation=formation,
            counter_defense="Base defense — read and react",
            adjustments=["Stay in your base defense until you identify tendencies"],
            key="Dont overreact to an unknown formation — play sound football",
        )


# Module-level singleton
formation_recognition = FormationRecognition()

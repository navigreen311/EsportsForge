"""ReadAI — Pre-snap coverage/blitz identification and pattern recognition for Madden 26.

Reads defensive alignments to identify coverage shells, detect blitzes,
recognize opponent tendencies, and suggest audibles.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.madden26.matchup import (
    Audible,
    BlitzRead,
    BlitzSource,
    ConfidenceLevel,
    CoverageRead,
    CoverageType,
    TendencyPattern,
)
from app.schemas.madden26.roster import MismatchSeverity

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Coverage identification rules
# ---------------------------------------------------------------------------

_COVERAGE_RULES: list[dict[str, Any]] = [
    {
        "coverage": CoverageType.COVER_0,
        "indicators": ["Single high safety in the box", "All DBs in press alignment", "No deep safety"],
        "required": {"safety_count_deep": 0, "press": True},
        "vulnerable_zones": ["Deep middle", "Deep sideline"],
        "targets": ["Go route", "Post", "Any deep route — no safety help"],
    },
    {
        "coverage": CoverageType.COVER_1,
        "indicators": ["Single high safety", "CBs in press or off-man", "LBs showing man on RB/TE"],
        "required": {"safety_count_deep": 1, "press": True},
        "vulnerable_zones": ["Deep sideline opposite safety shade", "Hole between LBs"],
        "targets": ["Post", "Corner route", "TE seam"],
    },
    {
        "coverage": CoverageType.COVER_2,
        "indicators": ["Two deep safeties split", "CBs playing flat zones", "LBs in hook/curl zones"],
        "required": {"safety_count_deep": 2, "press": False},
        "vulnerable_zones": ["Deep middle (hole shot)", "Sideline between CB flat and safety deep half"],
        "targets": ["Four Verticals", "Smash concept", "TE seam up the middle"],
    },
    {
        "coverage": CoverageType.COVER_3,
        "indicators": ["Single high safety", "CBs bailing at snap", "LBs dropping to curl/flat"],
        "required": {"safety_count_deep": 1, "press": False},
        "vulnerable_zones": ["Flat areas", "Curl/hook windows", "Seam between deep thirds"],
        "targets": ["Flood concept", "Curl/flat", "Corner route to the boundary"],
    },
    {
        "coverage": CoverageType.COVER_4,
        "indicators": ["Two deep safeties", "CBs playing deep quarter", "Soft coverage across the board"],
        "required": {"safety_count_deep": 2, "press": False, "soft_coverage": True},
        "vulnerable_zones": ["Underneath — hook, curl, flat", "Drag routes"],
        "targets": ["Mesh", "Dig/In routes", "HB checkdowns"],
    },
    {
        "coverage": CoverageType.COVER_6,
        "indicators": ["Split coverage — Cover 2 one side, Cover 4 other", "Asymmetric safety alignment"],
        "required": {"safety_count_deep": 2, "asymmetric": True},
        "vulnerable_zones": ["Cover-2 side deep middle", "Cover-4 side underneath"],
        "targets": ["Attack the Cover-2 side with smash/corner", "Underneath routes to Cover-4 side"],
    },
]

_BLITZ_INDICATORS: dict[BlitzSource, list[str]] = {
    BlitzSource.MLB: ["MLB creeping to A-gap", "MLB showing blitz pre-snap"],
    BlitzSource.OLB: ["OLB walked up on the edge", "OLB showing outside rush"],
    BlitzSource.CB: ["CB creeping toward LOS", "CB in press with no safety help"],
    BlitzSource.SS: ["SS in the box", "SS walking down pre-snap"],
    BlitzSource.FS: ["FS rotating down", "FS showing blitz from depth"],
    BlitzSource.DB_BLITZ: ["Multiple DBs near the LOS", "Overloaded side with DB pressure"],
}


# ---------------------------------------------------------------------------
# ReadAI
# ---------------------------------------------------------------------------

class ReadAI:
    """Pre-snap defensive read engine for Madden 26."""

    # ------------------------------------------------------------------
    # identify_coverage
    # ------------------------------------------------------------------

    def identify_coverage(self, pre_snap_info: dict[str, Any]) -> CoverageRead:
        """Identify the defensive coverage shell from pre-snap alignment cues.

        Expected keys in ``pre_snap_info``:
        - safety_count_deep (int): safeties 12+ yards deep
        - press (bool): are corners in press?
        - soft_coverage (bool): corners playing 7+ yards off?
        - asymmetric (bool): different coverage look on each side?
        - lb_depth (str): "shallow" | "medium" | "deep"
        """
        safety_deep = pre_snap_info.get("safety_count_deep", 1)
        press = pre_snap_info.get("press", False)
        soft = pre_snap_info.get("soft_coverage", False)
        asymmetric = pre_snap_info.get("asymmetric", False)

        best_match = _COVERAGE_RULES[3]  # default Cover 3
        best_score = 0

        for rule in _COVERAGE_RULES:
            req = rule["required"]
            score = 0

            if req.get("safety_count_deep") == safety_deep:
                score += 3
            if req.get("press", None) is not None and req["press"] == press:
                score += 2
            if req.get("soft_coverage", None) is not None and req["soft_coverage"] == soft:
                score += 1
            if req.get("asymmetric", None) is not None and req["asymmetric"] == asymmetric:
                score += 1

            if score > best_score:
                best_score = score
                best_match = rule

        confidence = ConfidenceLevel.HIGH if best_score >= 5 else (
            ConfidenceLevel.MEDIUM if best_score >= 3 else ConfidenceLevel.LOW
        )

        return CoverageRead(
            primary_coverage=best_match["coverage"],
            confidence=confidence,
            indicators=best_match["indicators"],
            vulnerable_zones=best_match["vulnerable_zones"],
            recommended_targets=best_match["targets"],
        )

    # ------------------------------------------------------------------
    # identify_blitz
    # ------------------------------------------------------------------

    def identify_blitz(self, pre_snap_info: dict[str, Any]) -> BlitzRead:
        """Detect whether a blitz is coming and from where.

        Expected keys:
        - defenders_near_los (int): defenders within 3 yards of the LOS
        - blitz_indicators (list[str]): raw cues like "SS in the box"
        - rushed_last_play (int): number of rushers on the previous play
        """
        near_los = pre_snap_info.get("defenders_near_los", 4)
        indicators_raw: list[str] = pre_snap_info.get("blitz_indicators", [])
        rushed_last = pre_snap_info.get("rushed_last_play", 4)

        blitz_prob = 0.0
        likely_source = BlitzSource.NONE
        detected_indicators: list[str] = []

        # Count rushers as a signal
        if near_los >= 6:
            blitz_prob += 0.4
        elif near_los >= 5:
            blitz_prob += 0.25

        # Historical tendency
        if rushed_last >= 6:
            blitz_prob += 0.15

        # Match indicator strings to known blitz sources
        best_source_score = 0
        for source, known_indicators in _BLITZ_INDICATORS.items():
            matches = [i for i in indicators_raw if any(k.lower() in i.lower() for k in known_indicators)]
            if len(matches) > best_source_score:
                best_source_score = len(matches)
                likely_source = source
                detected_indicators = matches

        if best_source_score:
            blitz_prob += 0.2 * best_source_score

        blitz_prob = min(blitz_prob, 1.0)
        blitz_detected = blitz_prob >= 0.5
        num_rushers = min(near_los, 8) if blitz_detected else max(near_los, 4)

        hot_route = None
        protection = None
        if blitz_detected:
            hot_route = self._hot_route_for_blitz(likely_source)
            protection = self._protection_for_blitz(likely_source, num_rushers)

        return BlitzRead(
            blitz_detected=blitz_detected,
            blitz_probability=round(blitz_prob, 2),
            likely_source=likely_source,
            number_of_rushers=max(3, min(num_rushers, 8)),
            hot_route_suggestion=hot_route,
            protection_adjustment=protection,
            indicators=detected_indicators or indicators_raw,
        )

    # ------------------------------------------------------------------
    # get_pattern_recognition
    # ------------------------------------------------------------------

    def get_pattern_recognition(
        self,
        opponent_history: list[dict[str, Any]],
    ) -> list[TendencyPattern]:
        """Analyze opponent play history to detect tendencies.

        Each entry in ``opponent_history`` should have:
        - situation (str): e.g. "3rd_and_long", "red_zone"
        - play_type (str): e.g. "pass", "run", "blitz"
        - formation (str): optional
        """
        if not opponent_history:
            return []

        # Group by situation
        situation_groups: dict[str, list[dict]] = {}
        for entry in opponent_history:
            sit = entry.get("situation", "general")
            situation_groups.setdefault(sit, []).append(entry)

        patterns: list[TendencyPattern] = []
        for situation, plays in situation_groups.items():
            total = len(plays)
            if total < 3:
                continue

            # Count play_type frequencies
            type_counts: dict[str, int] = {}
            for p in plays:
                pt = p.get("play_type", "unknown")
                type_counts[pt] = type_counts.get(pt, 0) + 1

            for play_type, count in type_counts.items():
                freq = count / total
                if freq < 0.4:
                    continue  # Only flag strong tendencies

                confidence = ConfidenceLevel.VERY_HIGH if freq >= 0.75 else (
                    ConfidenceLevel.HIGH if freq >= 0.6 else ConfidenceLevel.MEDIUM
                )

                counter = self._counter_for_tendency(play_type, situation)

                patterns.append(TendencyPattern(
                    pattern_name=f"{play_type.title()} heavy on {situation.replace('_', ' ')}",
                    description=(
                        f"Opponent runs {play_type} {freq:.0%} of the time "
                        f"in {situation.replace('_', ' ')} situations."
                    ),
                    frequency=round(freq, 2),
                    situation=situation,
                    counter_strategy=counter,
                    sample_size=total,
                    confidence=confidence,
                ))

        return sorted(patterns, key=lambda p: p.frequency, reverse=True)

    # ------------------------------------------------------------------
    # suggest_audible
    # ------------------------------------------------------------------

    def suggest_audible(
        self,
        coverage_read: CoverageRead,
        current_play: str,
    ) -> Audible:
        """Recommend the best audible given a coverage read and the called play."""
        coverage = coverage_read.primary_coverage
        audible_map: dict[CoverageType, dict[str, str]] = {
            CoverageType.COVER_0: {
                "audible": "Quick Slants",
                "reason": "No deep safety — quick throws beat the blitz",
                "gain": "5-15 yards, potential YAC",
            },
            CoverageType.COVER_1: {
                "audible": "Post Route / Corner Route",
                "reason": "Single high — attack the sideline away from the safety",
                "gain": "15-30 yards deep shot",
            },
            CoverageType.COVER_2: {
                "audible": "Four Verticals",
                "reason": "Split safeties — attack the deep middle hole",
                "gain": "20+ yard hole shot",
            },
            CoverageType.COVER_3: {
                "audible": "Flood Concept",
                "reason": "Three deep — overload the flat and curl zones",
                "gain": "8-15 yards to the flat or curl",
            },
            CoverageType.COVER_4: {
                "audible": "Mesh / Drive Concept",
                "reason": "Quarters coverage drops deep — attack underneath",
                "gain": "5-10 yards on crossing routes",
            },
            CoverageType.COVER_6: {
                "audible": "Smash to Cover-2 Side",
                "reason": "Exploit the Cover-2 half with a corner route",
                "gain": "15-25 yards to the sideline",
            },
        }

        default = {
            "audible": "HB Screen",
            "reason": "Safe checkdown against ambiguous coverage",
            "gain": "3-8 yards with blockers",
        }

        recommendation = audible_map.get(coverage, default)
        conf = coverage_read.confidence

        risk = MismatchSeverity.LOW
        if conf == ConfidenceLevel.LOW:
            risk = MismatchSeverity.HIGH
        elif conf == ConfidenceLevel.MEDIUM:
            risk = MismatchSeverity.MEDIUM

        return Audible(
            original_play=current_play,
            audible_to=recommendation["audible"],
            reason=recommendation["reason"],
            expected_gain=recommendation["gain"],
            confidence=conf,
            risk_level=risk,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hot_route_for_blitz(source: BlitzSource) -> str:
        routes: dict[BlitzSource, str] = {
            BlitzSource.MLB: "TE or HB hot route up the A-gap vacated by the blitzing MLB",
            BlitzSource.OLB: "Quick out route to the side the OLB vacated",
            BlitzSource.CB: "Quick slant behind the blitzing CB",
            BlitzSource.SS: "Deep post — SS vacated the deep half",
            BlitzSource.FS: "Skinny post or dig — FS left the middle",
            BlitzSource.DB_BLITZ: "Quick screen or slant — DBs are committing to rush",
            BlitzSource.SIMULATED: "Wait and read — simulated blitz may drop back",
            BlitzSource.NONE: "No hot route needed",
        }
        return routes.get(source, "Quick slant as a safe hot route")

    @staticmethod
    def _protection_for_blitz(source: BlitzSource, rushers: int) -> str:
        if rushers >= 7:
            return "Max protect — keep TE and HB in to block, throw hot"
        if rushers >= 6:
            return "Slide protection toward the blitz side, HB chip and release"
        if source in (BlitzSource.CB, BlitzSource.DB_BLITZ):
            return "ID the blitzing DB, slide away, throw quick to the vacated area"
        if source in (BlitzSource.SS, BlitzSource.FS):
            return "RB stays in to pick up the safety, look deep to the vacated zone"
        return "Slide protection toward the pressure side"

    @staticmethod
    def _counter_for_tendency(play_type: str, situation: str) -> str:
        counters: dict[str, str] = {
            "pass": "Bring pressure — blitz or show blitz to force quick throws. Play tight coverage.",
            "run": "Stack the box — bring a safety down. Pinch the D-line.",
            "blitz": "Quick passes, screens, and max protect. Make them pay for leaving gaps.",
            "deep_pass": "Play two-deep shells. Keep everything in front of you.",
            "screen": "Crash D-line — pursue laterally. LBs read and react to the screen.",
        }
        return counters.get(play_type, f"Adjust formation to counter {play_type} tendency in {situation}.")

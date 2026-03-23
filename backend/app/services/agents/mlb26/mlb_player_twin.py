"""MLB PlayerTwin — pitch recognition profiling, hitting zone maps, and clutch RISP analysis.

Builds a digital model of the MLB The Show 26 player, tracking pitch recognition
ability, mapping strengths/weaknesses by zone, and measuring clutch performance
with runners in scoring position.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from app.schemas.mlb26.hitting import (
    ClutchProfile,
    MLBTwinProfile,
    PitchRecognition,
    ZoneProfile,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pitch recognition model
# ---------------------------------------------------------------------------

_PITCH_RECOGNITION_THRESHOLDS: dict[str, float] = {
    "elite": 0.80,
    "strong": 0.65,
    "average": 0.50,
    "developing": 0.35,
}


class MLBPlayerTwin:
    """Digital twin for MLB The Show 26 players.

    Tracks pitch recognition ability, builds zone performance maps,
    and analyzes clutch hitting with runners in scoring position.
    """

    def __init__(self) -> None:
        self._at_bat_history: dict[str, list[dict[str, Any]]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Pitch recognition
    # ------------------------------------------------------------------

    def evaluate_pitch_recognition(
        self,
        user_id: str,
        pitch_log: list[dict[str, Any]],
    ) -> PitchRecognition:
        """Evaluate the player's pitch recognition ability from a log of pitches seen.

        Expected keys per entry: pitch_type, zone, swing (bool), result, count,
        was_ball (bool), was_chase (bool).
        """
        self._at_bat_history[user_id].extend(pitch_log)
        history = self._at_bat_history[user_id]
        total = len(history)

        if total == 0:
            return PitchRecognition(
                user_id=user_id, sample_size=0, overall_grade="unknown",
                chase_rate=0.0, take_rate_on_balls=0.0,
                pitch_type_recognition={}, notes=["No data available."],
            )

        # Chase rate: swinging at pitches outside the zone
        balls = [p for p in history if p.get("was_ball")]
        chases = [p for p in balls if p.get("swing")]
        chase_rate = len(chases) / max(len(balls), 1)

        # Take rate on balls (correct takes)
        takes_on_balls = len(balls) - len(chases)
        take_rate = takes_on_balls / max(len(balls), 1)

        # Per-pitch-type recognition
        pitch_groups: dict[str, dict[str, int]] = defaultdict(lambda: {"seen": 0, "correct": 0})
        for p in history:
            pt = p.get("pitch_type", "unknown")
            pitch_groups[pt]["seen"] += 1
            # Correct decision: take a ball or swing at a strike in the zone
            was_ball = p.get("was_ball", False)
            swung = p.get("swing", False)
            if (was_ball and not swung) or (not was_ball and swung and p.get("zone", 5) <= 9):
                pitch_groups[pt]["correct"] += 1

        pitch_recognition: dict[str, float] = {}
        for pt, counts in pitch_groups.items():
            pitch_recognition[pt] = round(counts["correct"] / max(counts["seen"], 1), 3)

        # Overall grade
        avg_recognition = sum(pitch_recognition.values()) / max(len(pitch_recognition), 1)
        grade = "developing"
        for label, threshold in _PITCH_RECOGNITION_THRESHOLDS.items():
            if avg_recognition >= threshold:
                grade = label
                break

        notes: list[str] = []
        if chase_rate > 0.35:
            notes.append(f"Chase rate is {chase_rate:.0%} — lay off pitches outside the zone.")
        if chase_rate < 0.20:
            notes.append(f"Excellent plate discipline — {chase_rate:.0%} chase rate.")

        # Find weakest pitch type
        worst_pitch = min(pitch_recognition, key=pitch_recognition.get) if pitch_recognition else None  # type: ignore[arg-type]
        if worst_pitch and pitch_recognition[worst_pitch] < 0.45:
            notes.append(f"Weakest recognition: {worst_pitch} ({pitch_recognition[worst_pitch]:.0%}) — practice identifying this pitch.")

        return PitchRecognition(
            user_id=user_id,
            sample_size=total,
            overall_grade=grade,
            chase_rate=round(chase_rate, 3),
            take_rate_on_balls=round(take_rate, 3),
            pitch_type_recognition=pitch_recognition,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Hitting zone profile
    # ------------------------------------------------------------------

    def build_zone_profile(
        self,
        user_id: str,
    ) -> ZoneProfile:
        """Build a 9-zone hitting profile from accumulated at-bat data.

        Maps each zone to batting average, slug percentage, and whiff rate.
        """
        history = self._at_bat_history.get(user_id, [])
        zone_data: dict[int, dict[str, int]] = defaultdict(lambda: {"abs": 0, "hits": 0, "xbh": 0, "whiffs": 0})

        for entry in history:
            zone = entry.get("zone", 5)
            if zone < 1 or zone > 9:
                continue  # Only track strike zone
            if not entry.get("swing"):
                continue

            zone_data[zone]["abs"] += 1
            result = entry.get("result", "out")
            if result in ("single", "double", "triple", "homer"):
                zone_data[zone]["hits"] += 1
            if result in ("double", "triple", "homer"):
                zone_data[zone]["xbh"] += 1
            if result in ("whiff", "strike_swinging"):
                zone_data[zone]["whiffs"] += 1

        zones: dict[int, dict[str, float]] = {}
        hot_zones: list[int] = []
        cold_zones: list[int] = []

        for z in range(1, 10):
            d = zone_data[z]
            ab = d["abs"]
            if ab == 0:
                zones[z] = {"avg": 0.0, "slg": 0.0, "whiff_rate": 0.0, "sample": 0}
                continue

            avg = d["hits"] / ab
            # Simplified slugging
            total_bases = d["hits"] + d["xbh"]  # approximation
            slg = total_bases / ab
            whiff_rate = d["whiffs"] / ab

            zones[z] = {
                "avg": round(avg, 3),
                "slg": round(slg, 3),
                "whiff_rate": round(whiff_rate, 3),
                "sample": ab,
            }

            if ab >= 5 and avg >= 0.300:
                hot_zones.append(z)
            elif ab >= 5 and avg < 0.150:
                cold_zones.append(z)

        return ZoneProfile(
            user_id=user_id,
            zones=zones,
            hot_zones=hot_zones,
            cold_zones=cold_zones,
            sample_size=len(history),
            recommendation=(
                f"Attack zones {hot_zones} — your batting average is elite there."
                if hot_zones
                else "Accumulate more at-bats to identify your hot zones."
            ),
        )

    # ------------------------------------------------------------------
    # Clutch RISP analysis
    # ------------------------------------------------------------------

    def analyze_clutch_risp(
        self,
        user_id: str,
        at_bats: list[dict[str, Any]],
    ) -> ClutchProfile:
        """Analyze clutch performance with runners in scoring position.

        Expected keys: risp (bool), result, inning, outs, score_diff, leverage.
        """
        self._at_bat_history[user_id].extend(at_bats)

        risp_abs = [ab for ab in self._at_bat_history[user_id] if ab.get("risp")]
        non_risp = [ab for ab in self._at_bat_history[user_id] if not ab.get("risp")]

        risp_total = len(risp_abs)
        risp_hits = sum(1 for ab in risp_abs if ab.get("result") in ("single", "double", "triple", "homer"))
        risp_avg = risp_hits / max(risp_total, 1)

        non_risp_total = len(non_risp)
        non_risp_hits = sum(1 for ab in non_risp if ab.get("result") in ("single", "double", "triple", "homer"))
        non_risp_avg = non_risp_hits / max(non_risp_total, 1)

        clutch_diff = risp_avg - non_risp_avg

        # Late-inning pressure
        late_close = [
            ab for ab in risp_abs
            if ab.get("inning", 1) >= 7 and abs(ab.get("score_diff", 0)) <= 2
        ]
        late_close_hits = sum(1 for ab in late_close if ab.get("result") in ("single", "double", "triple", "homer"))
        late_close_avg = late_close_hits / max(len(late_close), 1)

        # Determine clutch grade
        if clutch_diff >= 0.05 and risp_avg >= 0.300:
            grade = "clutch"
        elif clutch_diff <= -0.05 and risp_avg < 0.200:
            grade = "chokes_under_pressure"
        elif risp_avg >= 0.250:
            grade = "steady"
        else:
            grade = "developing"

        notes: list[str] = []
        if grade == "clutch":
            notes.append(f"Hits {risp_avg:.3f} with RISP vs {non_risp_avg:.3f} overall — true clutch performer.")
        elif grade == "chokes_under_pressure":
            notes.append(f"RISP avg ({risp_avg:.3f}) drops significantly from overall ({non_risp_avg:.3f}).")
            notes.append("Practice high-leverage at-bats. Focus on breathing and pitch selection under pressure.")
        if late_close:
            notes.append(f"Late & close RISP: {late_close_avg:.3f} in {len(late_close)} ABs.")

        return ClutchProfile(
            user_id=user_id,
            risp_avg=round(risp_avg, 3),
            non_risp_avg=round(non_risp_avg, 3),
            clutch_diff=round(clutch_diff, 3),
            late_close_avg=round(late_close_avg, 3),
            grade=grade,
            risp_sample=risp_total,
            notes=notes,
        )


# Module-level singleton
mlb_player_twin = MLBPlayerTwin()

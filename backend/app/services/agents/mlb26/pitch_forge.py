"""PitchForge — pitch sequencing AI, tunnel trainer, and batter tendency analysis.

Generates optimal pitch sequences, identifies tunneling opportunities,
and scouts batter tendencies to maximize strikeout probability.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from app.schemas.mlb26.pitching import (
    BatterTendency,
    PitchLocation,
    PitchSequence,
    PitchType,
    SequenceStrategy,
    TunnelPair,
    TunnelReport,
    ZoneHeatmap,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pitch arsenal data
# ---------------------------------------------------------------------------

_PITCH_DATA: dict[PitchType, dict[str, Any]] = {
    PitchType.FOUR_SEAM: {
        "avg_velo": 95.0, "movement_h": 0.0, "movement_v": 12.0,
        "whiff_rate": 0.22, "tunnel_group": "fastball",
    },
    PitchType.TWO_SEAM: {
        "avg_velo": 93.0, "movement_h": 8.0, "movement_v": 8.0,
        "whiff_rate": 0.18, "tunnel_group": "fastball",
    },
    PitchType.CUTTER: {
        "avg_velo": 89.0, "movement_h": -3.0, "movement_v": 6.0,
        "whiff_rate": 0.25, "tunnel_group": "fastball",
    },
    PitchType.SLIDER: {
        "avg_velo": 85.0, "movement_h": -6.0, "movement_v": 2.0,
        "whiff_rate": 0.32, "tunnel_group": "breaking",
    },
    PitchType.CURVEBALL: {
        "avg_velo": 79.0, "movement_h": -4.0, "movement_v": -8.0,
        "whiff_rate": 0.30, "tunnel_group": "breaking",
    },
    PitchType.CHANGEUP: {
        "avg_velo": 85.0, "movement_h": 6.0, "movement_v": 4.0,
        "whiff_rate": 0.28, "tunnel_group": "offspeed",
    },
    PitchType.SINKER: {
        "avg_velo": 94.0, "movement_h": 10.0, "movement_v": 4.0,
        "whiff_rate": 0.16, "tunnel_group": "fastball",
    },
    PitchType.SPLITTER: {
        "avg_velo": 87.0, "movement_h": 4.0, "movement_v": -4.0,
        "whiff_rate": 0.34, "tunnel_group": "offspeed",
    },
    PitchType.KNUCKLE_CURVE: {
        "avg_velo": 77.0, "movement_h": -2.0, "movement_v": -10.0,
        "whiff_rate": 0.28, "tunnel_group": "breaking",
    },
}

# Zone numbering: 1-9 strike zone (3x3 grid), 10-13 chase zones, 14 waste
_ZONE_LABELS: dict[int, str] = {
    1: "Up-In", 2: "Up-Mid", 3: "Up-Away",
    4: "Mid-In", 5: "Heart", 6: "Mid-Away",
    7: "Low-In", 8: "Low-Mid", 9: "Low-Away",
    10: "Chase-Up", 11: "Chase-In", 12: "Chase-Down", 13: "Chase-Away",
    14: "Waste",
}

# Typical batter weaknesses by handedness
_BATTER_WEAKNESSES: dict[str, list[int]] = {
    "RHH": [9, 12, 13],  # low-away, chase-down, chase-away
    "LHH": [7, 11, 12],  # low-in (from RHP perspective), chase-in, chase-down
}


class PitchForge:
    """MLB The Show 26 pitch sequencing and tunneling engine.

    Builds optimal pitch sequences, identifies tunnel pairs, and
    analyzes batter tendencies for strikeout strategy.
    """

    def __init__(self) -> None:
        self._batter_history: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._sequence_cache: dict[str, PitchSequence] = {}

    # ------------------------------------------------------------------
    # Pitch sequencing
    # ------------------------------------------------------------------

    def generate_sequence(
        self,
        arsenal: list[PitchType],
        batter_hand: str = "RHH",
        count: str = "0-0",
        outs: int = 0,
        runners_on: bool = False,
    ) -> PitchSequence:
        """Generate an optimal 3-5 pitch sequence for the at-bat.

        Considers the pitcher's arsenal, batter handedness, count leverage,
        and game situation to build a sequence that maximizes K probability.
        """
        if not arsenal:
            arsenal = [PitchType.FOUR_SEAM, PitchType.SLIDER, PitchType.CHANGEUP]

        # Build sequence based on situation
        pitches: list[dict[str, Any]] = []
        weak_zones = _BATTER_WEAKNESSES.get(batter_hand, [9, 12])

        # Pitch 1: Establish the fastball
        fb = self._best_fastball(arsenal)
        pitches.append({
            "pitch_number": 1,
            "pitch_type": fb.value,
            "target_zone": 5 if count == "0-0" else 2,
            "intent": "establish",
            "notes": "Show the fastball early — set up the tunnel.",
        })

        # Pitch 2: Same tunnel, different movement
        off = self._best_offspeed(arsenal)
        pitches.append({
            "pitch_number": 2,
            "pitch_type": off.value,
            "target_zone": weak_zones[0] if weak_zones else 8,
            "intent": "tunnel",
            "notes": f"Tunnel off the fastball — same release point, different break.",
        })

        # Pitch 3: Expand the zone
        breaking = self._best_breaking(arsenal)
        chase_zone = weak_zones[1] if len(weak_zones) > 1 else 12
        pitches.append({
            "pitch_number": 3,
            "pitch_type": breaking.value if breaking else off.value,
            "target_zone": chase_zone,
            "intent": "chase",
            "notes": "Expand — get the swing and miss outside the zone.",
        })

        # Pitch 4 (if needed): Come back with heat
        if outs < 2 or runners_on:
            pitches.append({
                "pitch_number": 4,
                "pitch_type": fb.value,
                "target_zone": 2 if batter_hand == "RHH" else 3,
                "intent": "finish",
                "notes": "Elevated fastball to finish — batter expecting offspeed.",
            })

        # Compute aggregate K probability
        whiff_sum = sum(
            _PITCH_DATA.get(PitchType(p["pitch_type"]), {}).get("whiff_rate", 0.2)
            for p in pitches
        )
        k_prob = min(0.85, whiff_sum / len(pitches) + 0.15)

        strategy = SequenceStrategy.TUNNEL
        if runners_on and outs < 2:
            strategy = SequenceStrategy.GROUNDBALL
        elif count in ("0-2", "1-2"):
            strategy = SequenceStrategy.PUTAWAY

        return PitchSequence(
            pitches=pitches,
            strategy=strategy,
            strikeout_probability=round(k_prob, 3),
            batter_hand=batter_hand,
            count=count,
            notes=f"Sequence built for {batter_hand} in {count} count, {outs} outs.",
        )

    # ------------------------------------------------------------------
    # Tunnel trainer
    # ------------------------------------------------------------------

    def find_tunnel_pairs(self, arsenal: list[PitchType]) -> TunnelReport:
        """Identify the best tunneling pairs from a pitcher's arsenal.

        Tunnel pairs are pitches that look identical out of the hand but
        diverge in movement, creating deception.
        """
        pairs: list[TunnelPair] = []

        for i, pitch_a in enumerate(arsenal):
            data_a = _PITCH_DATA.get(pitch_a, {})
            group_a = data_a.get("tunnel_group", "unknown")

            for pitch_b in arsenal[i + 1:]:
                data_b = _PITCH_DATA.get(pitch_b, {})
                group_b = data_b.get("tunnel_group", "unknown")

                # Different groups create better tunnels
                if group_a == group_b:
                    continue

                velo_diff = abs(data_a.get("avg_velo", 90) - data_b.get("avg_velo", 90))
                h_diff = abs(data_a.get("movement_h", 0) - data_b.get("movement_h", 0))
                v_diff = abs(data_a.get("movement_v", 0) - data_b.get("movement_v", 0))

                # Tunnel score: high movement difference + moderate velo difference
                tunnel_score = (h_diff + v_diff) * 0.05 + min(velo_diff, 12) * 0.02
                tunnel_score = min(1.0, tunnel_score)

                deception_rating = "elite" if tunnel_score >= 0.7 else (
                    "strong" if tunnel_score >= 0.5 else "average"
                )

                pairs.append(TunnelPair(
                    pitch_a=pitch_a,
                    pitch_b=pitch_b,
                    tunnel_score=round(tunnel_score, 3),
                    velo_diff=round(velo_diff, 1),
                    movement_diff_h=round(h_diff, 1),
                    movement_diff_v=round(v_diff, 1),
                    deception_rating=deception_rating,
                    description=(
                        f"{pitch_a.value} → {pitch_b.value}: "
                        f"{velo_diff:.0f} mph velo diff, "
                        f"{h_diff:.0f}\" horizontal + {v_diff:.0f}\" vertical separation."
                    ),
                ))

        pairs.sort(key=lambda p: p.tunnel_score, reverse=True)
        best = pairs[0] if pairs else None

        return TunnelReport(
            arsenal=arsenal,
            pairs=pairs,
            best_pair=best,
            recommendation=(
                f"Lead with {best.pitch_a.value}, tunnel into {best.pitch_b.value}"
                if best else "Add more pitch variety for tunnel options."
            ),
        )

    # ------------------------------------------------------------------
    # Batter tendency analysis
    # ------------------------------------------------------------------

    def analyze_batter_tendencies(
        self,
        batter_id: str,
        at_bat_history: list[dict[str, Any]],
    ) -> BatterTendency:
        """Analyze a batter's tendencies from pitch-by-pitch history.

        Expected keys per entry: pitch_type, zone, result (ball/strike/foul/hit/out),
        swing (bool), count.
        """
        self._batter_history[batter_id].extend(at_bat_history)
        history = self._batter_history[batter_id]

        if not history:
            return BatterTendency(
                batter_id=batter_id,
                sample_size=0,
                hot_zones=[],
                cold_zones=[],
                chase_rate=0.0,
                whiff_pitches=[],
                tendency_notes=["No data available."],
            )

        total = len(history)
        zone_results: dict[int, dict[str, int]] = defaultdict(lambda: {"swing": 0, "hit": 0, "total": 0})
        pitch_whiffs: dict[str, int] = defaultdict(int)
        pitch_swings: dict[str, int] = defaultdict(int)
        chase_count = 0

        for entry in history:
            zone = entry.get("zone", 5)
            swing = entry.get("swing", False)
            result = entry.get("result", "ball")
            pitch_type = entry.get("pitch_type", "unknown")

            zone_results[zone]["total"] += 1
            if swing:
                zone_results[zone]["swing"] += 1
                pitch_swings[pitch_type] += 1
                if result in ("whiff", "strike_swinging"):
                    pitch_whiffs[pitch_type] += 1
                if zone >= 10:  # chase zones
                    chase_count += 1

            if result in ("hit", "single", "double", "triple", "homer"):
                zone_results[zone]["hit"] += 1

        # Hot zones: high hit rate
        hot_zones = [
            z for z in range(1, 10)
            if zone_results[z]["total"] >= 3
            and zone_results[z]["hit"] / zone_results[z]["total"] >= 0.3
        ]
        # Cold zones: low hit rate with swings
        cold_zones = [
            z for z in range(1, 10)
            if zone_results[z]["total"] >= 3
            and zone_results[z]["hit"] / zone_results[z]["total"] < 0.15
            and zone_results[z]["swing"] / zone_results[z]["total"] > 0.5
        ]

        # Chase rate
        out_of_zone_pitches = sum(zone_results[z]["total"] for z in range(10, 15))
        chase_rate = chase_count / max(out_of_zone_pitches, 1)

        # Whiff pitches
        whiff_pitches = [
            pt for pt, swings in pitch_swings.items()
            if swings >= 3 and pitch_whiffs[pt] / swings >= 0.35
        ]

        notes: list[str] = []
        if chase_rate > 0.35:
            notes.append(f"High chase rate ({chase_rate:.0%}) — expand with breaking balls.")
        if hot_zones:
            notes.append(f"Hot zones: {[_ZONE_LABELS.get(z, z) for z in hot_zones]} — avoid these areas.")
        if cold_zones:
            notes.append(f"Cold zones: {[_ZONE_LABELS.get(z, z) for z in cold_zones]} — attack here.")

        return BatterTendency(
            batter_id=batter_id,
            sample_size=total,
            hot_zones=hot_zones,
            cold_zones=cold_zones,
            chase_rate=round(chase_rate, 3),
            whiff_pitches=whiff_pitches,
            tendency_notes=notes,
        )

    # ------------------------------------------------------------------
    # Zone heatmap
    # ------------------------------------------------------------------

    def get_zone_heatmap(self, batter_id: str) -> ZoneHeatmap:
        """Generate a 9-zone heatmap of batter performance."""
        history = self._batter_history.get(batter_id, [])
        zones: dict[int, dict[str, float]] = {}

        for z in range(1, 10):
            zone_pitches = [h for h in history if h.get("zone") == z]
            total = len(zone_pitches)
            if total == 0:
                zones[z] = {"avg": 0.0, "swing_rate": 0.0, "contact_rate": 0.0}
                continue

            swings = sum(1 for p in zone_pitches if p.get("swing"))
            hits = sum(1 for p in zone_pitches if p.get("result") in ("hit", "single", "double", "triple", "homer"))
            contacts = sum(1 for p in zone_pitches if p.get("result") not in ("whiff", "strike_swinging", "ball"))

            zones[z] = {
                "avg": round(hits / max(total, 1), 3),
                "swing_rate": round(swings / total, 3),
                "contact_rate": round(contacts / max(swings, 1), 3),
            }

        return ZoneHeatmap(
            batter_id=batter_id,
            zones=zones,
            sample_size=len(history),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _best_fastball(arsenal: list[PitchType]) -> PitchType:
        fb_types = [PitchType.FOUR_SEAM, PitchType.TWO_SEAM, PitchType.SINKER, PitchType.CUTTER]
        for pt in fb_types:
            if pt in arsenal:
                return pt
        return arsenal[0]

    @staticmethod
    def _best_offspeed(arsenal: list[PitchType]) -> PitchType:
        os_types = [PitchType.CHANGEUP, PitchType.SPLITTER]
        for pt in os_types:
            if pt in arsenal:
                return pt
        return arsenal[-1]

    @staticmethod
    def _best_breaking(arsenal: list[PitchType]) -> PitchType | None:
        brk_types = [PitchType.SLIDER, PitchType.CURVEBALL, PitchType.KNUCKLE_CURVE]
        for pt in brk_types:
            if pt in arsenal:
                return pt
        return None


# Module-level singleton
pitch_forge = PitchForge()

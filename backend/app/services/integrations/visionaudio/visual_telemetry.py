"""VisualTelemetry — stick movement analysis and hesitation window detection.

Analyzes controller input patterns from visual telemetry data,
detects hesitation windows, and identifies decision-making patterns.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from app.schemas.visionaudio import (
    HesitationWindow,
    StickMovementAnalysis,
    TelemetryReport,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Telemetry thresholds
# ---------------------------------------------------------------------------

_HESITATION_THRESHOLD_MS = 150  # >150ms of no input = hesitation
_PANIC_INPUT_THRESHOLD = 8  # >8 direction changes in 500ms = panic
_OPTIMAL_REACTION_MS = 200  # Optimal reaction time benchmark


class VisualTelemetry:
    """Visual telemetry engine for controller input analysis.

    Detects stick movement patterns, hesitation windows, and
    decision-making quality from visual input data.
    """

    # ------------------------------------------------------------------
    # Stick movement analysis
    # ------------------------------------------------------------------

    def analyze_stick_movement(
        self,
        input_samples: list[dict[str, Any]],
        context: str = "general",
    ) -> StickMovementAnalysis:
        """Analyze stick movement patterns from input samples.

        Each sample: timestamp_ms, stick_x (-1 to 1), stick_y (-1 to 1), buttons.
        """
        if not input_samples:
            return StickMovementAnalysis(
                total_samples=0, avg_stick_magnitude=0, direction_changes=0,
                smoothness_score=0, notes=["No input data."],
            )

        total = len(input_samples)
        magnitudes: list[float] = []
        direction_changes = 0
        prev_angle: float | None = None

        for i, sample in enumerate(input_samples):
            sx = sample.get("stick_x", 0.0)
            sy = sample.get("stick_y", 0.0)
            mag = math.sqrt(sx ** 2 + sy ** 2)
            magnitudes.append(mag)

            if mag > 0.1:  # Dead zone filter
                angle = math.degrees(math.atan2(sy, sx))
                if prev_angle is not None:
                    angle_diff = abs(angle - prev_angle)
                    if angle_diff > 180:
                        angle_diff = 360 - angle_diff
                    if angle_diff > 30:  # Significant direction change
                        direction_changes += 1
                prev_angle = angle

        avg_magnitude = sum(magnitudes) / max(total, 1)

        # Smoothness: fewer direction changes per sample = smoother
        smoothness = max(0, 1.0 - (direction_changes / max(total, 1)) * 5)

        # Detect panic inputs
        panic_windows = self._detect_panic_windows(input_samples)

        # Dead zone time (stick at center)
        dead_zone_samples = sum(1 for m in magnitudes if m < 0.1)
        dead_zone_pct = dead_zone_samples / max(total, 1)

        notes: list[str] = []
        if smoothness < 0.4:
            notes.append("Erratic stick movement — focus on deliberate, smooth inputs.")
        elif smoothness > 0.8:
            notes.append("Excellent stick control — smooth and decisive movements.")
        if panic_windows > 2:
            notes.append(f"{panic_windows} panic input windows detected — slow down under pressure.")
        if dead_zone_pct > 0.3:
            notes.append(f"Stick idle {dead_zone_pct:.0%} of the time — consider more active movement.")
        if context == "shooting" and avg_magnitude > 0.7:
            notes.append("High stick magnitude during shooting — lighter touch for accuracy.")

        return StickMovementAnalysis(
            total_samples=total,
            avg_stick_magnitude=round(avg_magnitude, 3),
            direction_changes=direction_changes,
            smoothness_score=round(smoothness, 3),
            panic_windows=panic_windows,
            dead_zone_pct=round(dead_zone_pct, 3),
            context=context,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Hesitation window detection
    # ------------------------------------------------------------------

    def detect_hesitation_windows(
        self,
        input_samples: list[dict[str, Any]],
        game_events: list[dict[str, Any]] | None = None,
    ) -> list[HesitationWindow]:
        """Detect moments where the player hesitated before making a decision.

        Identifies gaps in input activity that indicate decision paralysis.
        """
        if not input_samples:
            return []

        windows: list[HesitationWindow] = []
        hesitation_start: float | None = None
        last_active_ts = input_samples[0].get("timestamp_ms", 0)

        for sample in input_samples:
            ts = sample.get("timestamp_ms", 0)
            sx = abs(sample.get("stick_x", 0.0))
            sy = abs(sample.get("stick_y", 0.0))
            buttons = sample.get("buttons", [])

            is_active = (sx > 0.1 or sy > 0.1 or len(buttons) > 0)

            if is_active:
                if hesitation_start is not None:
                    duration = ts - hesitation_start
                    if duration >= _HESITATION_THRESHOLD_MS:
                        # Find concurrent game event
                        context = "unknown"
                        if game_events:
                            concurrent = [
                                e for e in game_events
                                if abs(e.get("timestamp_ms", 0) - hesitation_start) < 500
                            ]
                            if concurrent:
                                context = concurrent[0].get("event", "unknown")

                        windows.append(HesitationWindow(
                            start_ms=hesitation_start,
                            end_ms=ts,
                            duration_ms=round(duration, 1),
                            context=context,
                            severity=self._classify_hesitation(duration),
                        ))
                    hesitation_start = None
                last_active_ts = ts
            else:
                if hesitation_start is None:
                    hesitation_start = ts

        # Classify and add recommendations
        for window in windows:
            if window.severity == "critical":
                window.recommendation = (
                    f"Hesitated for {window.duration_ms:.0f}ms during {window.context}. "
                    "Pre-decide your action before the moment arrives."
                )
            elif window.severity == "moderate":
                window.recommendation = (
                    f"Brief hesitation ({window.duration_ms:.0f}ms) during {window.context}. "
                    "Commit to your reads faster."
                )

        return windows

    # ------------------------------------------------------------------
    # Full telemetry report
    # ------------------------------------------------------------------

    def generate_report(
        self,
        input_samples: list[dict[str, Any]],
        game_events: list[dict[str, Any]] | None = None,
        context: str = "general",
    ) -> TelemetryReport:
        """Generate a comprehensive telemetry report combining all analyses."""
        stick_analysis = self.analyze_stick_movement(input_samples, context)
        hesitations = self.detect_hesitation_windows(input_samples, game_events)

        # Reaction time analysis
        reaction_times: list[float] = []
        if game_events and input_samples:
            for event in game_events:
                event_ts = event.get("timestamp_ms", 0)
                # Find first input after event
                first_input = next(
                    (s for s in input_samples
                     if s.get("timestamp_ms", 0) > event_ts
                     and (abs(s.get("stick_x", 0)) > 0.1 or s.get("buttons", []))),
                    None,
                )
                if first_input:
                    rt = first_input["timestamp_ms"] - event_ts
                    if 50 < rt < 2000:  # Filter outliers
                        reaction_times.append(rt)

        avg_reaction = sum(reaction_times) / max(len(reaction_times), 1) if reaction_times else 0

        return TelemetryReport(
            stick_analysis=stick_analysis,
            hesitations=hesitations,
            hesitation_count=len(hesitations),
            avg_reaction_time_ms=round(avg_reaction, 1),
            reaction_grade=self._grade_reaction(avg_reaction),
            context=context,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_panic_windows(samples: list[dict[str, Any]]) -> int:
        panic_count = 0
        window_size_ms = 500
        window_start = 0

        for i, sample in enumerate(samples):
            ts = sample.get("timestamp_ms", 0)
            if ts - window_start > window_size_ms:
                # Count direction changes in this window
                window_samples = [
                    s for s in samples
                    if window_start <= s.get("timestamp_ms", 0) <= ts
                ]
                changes = 0
                prev_x, prev_y = 0.0, 0.0
                for ws in window_samples:
                    sx = ws.get("stick_x", 0.0)
                    sy = ws.get("stick_y", 0.0)
                    if abs(sx - prev_x) > 0.5 or abs(sy - prev_y) > 0.5:
                        changes += 1
                    prev_x, prev_y = sx, sy

                if changes >= _PANIC_INPUT_THRESHOLD:
                    panic_count += 1
                window_start = ts

        return panic_count

    @staticmethod
    def _classify_hesitation(duration_ms: float) -> str:
        if duration_ms >= 500:
            return "critical"
        if duration_ms >= 300:
            return "moderate"
        return "minor"

    @staticmethod
    def _grade_reaction(avg_ms: float) -> str:
        if avg_ms == 0:
            return "no_data"
        if avg_ms <= 180:
            return "elite"
        if avg_ms <= 250:
            return "fast"
        if avg_ms <= 350:
            return "average"
        return "slow"


# Module-level singleton
visual_telemetry = VisualTelemetry()

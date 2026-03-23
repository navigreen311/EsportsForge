"""Per-input-type diagnostic adapters for InputLab.

Each adapter has its own latency assumptions, elite benchmarks,
and drill generators — no shared logic between input types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.input_lab import (
    DrillSpec,
    EliteBenchmark,
    InputEvent,
    InputType,
    MechanicalLeak,
)


class BaseInputAdapter(ABC):
    """Interface that every input-type adapter must implement."""

    input_type: InputType

    # Latency budget (ms) — how much inherent device latency to account for
    base_latency_ms: float

    @abstractmethod
    def analyze_events(self, events: list[InputEvent]) -> list[MechanicalLeak]:
        """Detect mechanical leaks specific to this input type."""

    @abstractmethod
    def elite_benchmarks(self, skill: str) -> dict[str, float]:
        """Return elite-level reference numbers for the given skill."""

    @abstractmethod
    def generate_drill(self, leak: MechanicalLeak) -> DrillSpec:
        """Create a corrective drill tailored to the input type."""


# ---------------------------------------------------------------------------
# Controller Adapter
# ---------------------------------------------------------------------------

class ControllerAdapter(BaseInputAdapter):
    """Diagnostic engine for standard gamepads (Xbox / PlayStation / etc.).

    Focuses on stick efficiency, trigger timing, and bumper accuracy.
    """

    input_type = InputType.CONTROLLER
    base_latency_ms = 8.0  # Wireless controller baseline

    # Elite reference values (keyed by metric name)
    _elite_refs: dict[str, dict[str, float]] = {
        "stick_efficiency": {"avg": 0.88, "top_10_pct": 0.94},
        "trigger_timing_ms": {"avg": 45.0, "top_10_pct": 32.0},
        "bumper_accuracy": {"avg": 0.91, "top_10_pct": 0.97},
        "stick_deadzone_waste": {"avg": 0.06, "top_10_pct": 0.02},
        "simultaneous_input_speed_ms": {"avg": 18.0, "top_10_pct": 11.0},
    }

    def analyze_events(self, events: list[InputEvent]) -> list[MechanicalLeak]:
        leaks: list[MechanicalLeak] = []

        stick_events = [e for e in events if "stick" in e.input_name.lower()]
        trigger_events = [e for e in events if "trigger" in e.input_name.lower()]
        bumper_events = [e for e in events if "bumper" in e.input_name.lower()]

        # --- Stick deadzone waste ---
        if stick_events:
            tiny_moves = [
                e for e in stick_events
                if e.value is not None and abs(e.value) < 0.15
            ]
            waste_ratio = len(tiny_moves) / max(len(stick_events), 1)
            if waste_ratio > 0.10:
                leaks.append(
                    MechanicalLeak(
                        leak_type="wasted_input",
                        description="Excessive stick micro-movements inside deadzone — inputs register but produce no meaningful action",
                        frequency_per_minute=self._freq(tiny_moves, events),
                        impact_rating=min(waste_ratio * 2, 1.0),
                        affected_inputs=["left_stick", "right_stick"],
                        example_timestamps_ms=[e.timestamp_ms for e in tiny_moves[:5]],
                    )
                )

        # --- Trigger hesitation ---
        if trigger_events:
            hesitations = [
                e for e in trigger_events
                if e.duration_ms is not None and e.duration_ms > 120
            ]
            if len(hesitations) / max(len(trigger_events), 1) > 0.15:
                leaks.append(
                    MechanicalLeak(
                        leak_type="hesitation_window",
                        description="Trigger pulls held too long before committing — slow trigger commitment",
                        frequency_per_minute=self._freq(hesitations, events),
                        impact_rating=0.6,
                        affected_inputs=["left_trigger", "right_trigger"],
                        example_timestamps_ms=[e.timestamp_ms for e in hesitations[:5]],
                    )
                )

        # --- Ghost bumper presses ---
        if bumper_events:
            ghost = [e for e in bumper_events if e.duration_ms is not None and e.duration_ms < 15]
            if len(ghost) / max(len(bumper_events), 1) > 0.08:
                leaks.append(
                    MechanicalLeak(
                        leak_type="ghost_input",
                        description="Ultra-short bumper taps registering as unintended presses",
                        frequency_per_minute=self._freq(ghost, events),
                        impact_rating=0.5,
                        affected_inputs=["left_bumper", "right_bumper"],
                        example_timestamps_ms=[e.timestamp_ms for e in ghost[:5]],
                    )
                )

        return leaks

    def elite_benchmarks(self, skill: str) -> dict[str, float]:
        return self._elite_refs.get(skill, {"avg": 0.0, "top_10_pct": 0.0})

    def generate_drill(self, leak: MechanicalLeak) -> DrillSpec:
        drills: dict[str, DrillSpec] = {
            "wasted_input": DrillSpec(
                drill_name="Stick Precision Circles",
                target_leak="wasted_input",
                input_type=self.input_type,
                description="Trace full circles at the outer edge of stick travel without dipping below 80% deflection. Builds muscle memory for deliberate stick control.",
                duration_minutes=10,
                difficulty="intermediate",
                success_criteria="Complete 20 full rotations with <5% deadzone entries",
                repetitions=3,
                rest_between_reps_seconds=10,
            ),
            "hesitation_window": DrillSpec(
                drill_name="Trigger Snap Drill",
                target_leak="hesitation_window",
                input_type=self.input_type,
                description="On visual cue, snap trigger from rest to full pull in under 60ms. Trains decisive trigger commitment.",
                duration_minutes=8,
                difficulty="advanced",
                success_criteria="90% of pulls under 60ms with full travel",
                repetitions=5,
                rest_between_reps_seconds=5,
            ),
            "ghost_input": DrillSpec(
                drill_name="Bumper Isolation Taps",
                target_leak="ghost_input",
                input_type=self.input_type,
                description="Alternate bumper taps with deliberate 200ms hold windows. Eliminates accidental ghost taps.",
                duration_minutes=5,
                difficulty="beginner",
                success_criteria="Zero ghost inputs (<15ms) over 100 taps",
                repetitions=4,
                rest_between_reps_seconds=5,
            ),
        }
        return drills.get(
            leak.leak_type,
            DrillSpec(
                drill_name="General Controller Warm-Up",
                target_leak=leak.leak_type,
                input_type=self.input_type,
                description="General warm-up focusing on clean input registration across all controller surfaces.",
                duration_minutes=10,
                difficulty="beginner",
                success_criteria="Complete warm-up with minimal wasted inputs",
                repetitions=2,
                rest_between_reps_seconds=10,
            ),
        )

    # --- helpers ---

    @staticmethod
    def _freq(subset: list[InputEvent], all_events: list[InputEvent]) -> float:
        if not all_events or len(all_events) < 2:
            return 0.0
        duration_min = (all_events[-1].timestamp_ms - all_events[0].timestamp_ms) / 60_000
        if duration_min <= 0:
            return 0.0
        return len(subset) / duration_min


# ---------------------------------------------------------------------------
# KBM (Keyboard & Mouse) Adapter
# ---------------------------------------------------------------------------

class KBMAdapter(BaseInputAdapter):
    """Diagnostic engine for keyboard-and-mouse setups.

    Focuses on key press timing, mouse precision, and movement efficiency.
    """

    input_type = InputType.KBM
    base_latency_ms = 3.0  # Wired KBM baseline

    _elite_refs: dict[str, dict[str, float]] = {
        "key_press_timing_ms": {"avg": 38.0, "top_10_pct": 25.0},
        "mouse_precision": {"avg": 0.90, "top_10_pct": 0.96},
        "movement_efficiency": {"avg": 0.85, "top_10_pct": 0.93},
        "key_rollover_speed_ms": {"avg": 22.0, "top_10_pct": 14.0},
        "flick_accuracy": {"avg": 0.78, "top_10_pct": 0.91},
    }

    def analyze_events(self, events: list[InputEvent]) -> list[MechanicalLeak]:
        leaks: list[MechanicalLeak] = []

        key_events = [e for e in events if e.action in ("press", "release") and "mouse" not in e.input_name.lower()]
        mouse_events = [e for e in events if "mouse" in e.input_name.lower()]

        # --- Double-tap waste (pressing same key twice within 30ms) ---
        if key_events:
            double_taps: list[InputEvent] = []
            for i in range(1, len(key_events)):
                if (
                    key_events[i].input_name == key_events[i - 1].input_name
                    and key_events[i].action == "press"
                    and key_events[i - 1].action == "press"
                    and key_events[i].timestamp_ms - key_events[i - 1].timestamp_ms < 30
                ):
                    double_taps.append(key_events[i])

            if len(double_taps) / max(len(key_events), 1) > 0.05:
                leaks.append(
                    MechanicalLeak(
                        leak_type="ghost_input",
                        description="Unintentional double-tap key presses within 30ms — likely key chatter or nervous habit",
                        frequency_per_minute=self._freq(double_taps, events),
                        impact_rating=0.5,
                        affected_inputs=list({e.input_name for e in double_taps}),
                        example_timestamps_ms=[e.timestamp_ms for e in double_taps[:5]],
                    )
                )

        # --- Mouse over-correction (rapid direction reversals) ---
        if mouse_events:
            reversals: list[InputEvent] = []
            move_events = [e for e in mouse_events if e.action == "move" and e.value is not None]
            for i in range(2, len(move_events)):
                v0 = move_events[i - 2].value or 0
                v1 = move_events[i - 1].value or 0
                v2 = move_events[i].value or 0
                if (v0 > 0 and v1 < 0 and v2 > 0) or (v0 < 0 and v1 > 0 and v2 < 0):
                    reversals.append(move_events[i])

            if len(reversals) / max(len(move_events), 1) > 0.12:
                leaks.append(
                    MechanicalLeak(
                        leak_type="over_travel",
                        description="Frequent mouse over-corrections — overshooting target then snapping back",
                        frequency_per_minute=self._freq(reversals, events),
                        impact_rating=0.7,
                        affected_inputs=["mouse_x", "mouse_y"],
                        example_timestamps_ms=[e.timestamp_ms for e in reversals[:5]],
                    )
                )

        # --- Hesitation on movement keys ---
        if key_events:
            movement_keys = {"w", "a", "s", "d", "up", "down", "left", "right"}
            move_presses = [
                e for e in key_events
                if e.input_name.lower() in movement_keys
                and e.action == "press"
                and e.duration_ms is not None
                and e.duration_ms < 20
            ]
            if len(move_presses) / max(len(key_events), 1) > 0.10:
                leaks.append(
                    MechanicalLeak(
                        leak_type="hesitation_window",
                        description="Very short movement key taps suggesting indecisive directional input",
                        frequency_per_minute=self._freq(move_presses, events),
                        impact_rating=0.4,
                        affected_inputs=["w", "a", "s", "d"],
                        example_timestamps_ms=[e.timestamp_ms for e in move_presses[:5]],
                    )
                )

        return leaks

    def elite_benchmarks(self, skill: str) -> dict[str, float]:
        return self._elite_refs.get(skill, {"avg": 0.0, "top_10_pct": 0.0})

    def generate_drill(self, leak: MechanicalLeak) -> DrillSpec:
        drills: dict[str, DrillSpec] = {
            "ghost_input": DrillSpec(
                drill_name="Clean Tap Trainer",
                target_leak="ghost_input",
                input_type=self.input_type,
                description="Single-tap each key on cue with 200ms minimum gap. No double-taps allowed.",
                duration_minutes=8,
                difficulty="beginner",
                success_criteria="100 consecutive clean single-taps",
                repetitions=3,
                rest_between_reps_seconds=10,
            ),
            "over_travel": DrillSpec(
                drill_name="Mouse Tracking Rails",
                target_leak="over_travel",
                input_type=self.input_type,
                description="Track a moving target along a rail without overshooting. Start slow, increase speed.",
                duration_minutes=12,
                difficulty="advanced",
                success_criteria="Track target with <5% overshoot for 60 seconds",
                repetitions=4,
                rest_between_reps_seconds=15,
            ),
            "hesitation_window": DrillSpec(
                drill_name="WASD Commitment Drill",
                target_leak="hesitation_window",
                input_type=self.input_type,
                description="On directional cue, commit to full key press and hold for 200ms minimum. No tapping.",
                duration_minutes=6,
                difficulty="intermediate",
                success_criteria="95% of directional inputs held for 200ms+",
                repetitions=3,
                rest_between_reps_seconds=5,
            ),
        }
        return drills.get(
            leak.leak_type,
            DrillSpec(
                drill_name="KBM Fundamentals Warm-Up",
                target_leak=leak.leak_type,
                input_type=self.input_type,
                description="General keyboard-and-mouse warm-up focusing on clean registration.",
                duration_minutes=10,
                difficulty="beginner",
                success_criteria="Complete warm-up sequence cleanly",
                repetitions=2,
                rest_between_reps_seconds=10,
            ),
        )

    @staticmethod
    def _freq(subset: list[InputEvent], all_events: list[InputEvent]) -> float:
        if not all_events or len(all_events) < 2:
            return 0.0
        duration_min = (all_events[-1].timestamp_ms - all_events[0].timestamp_ms) / 60_000
        if duration_min <= 0:
            return 0.0
        return len(subset) / duration_min


# ---------------------------------------------------------------------------
# Fight Stick Adapter
# ---------------------------------------------------------------------------

class FightStickAdapter(BaseInputAdapter):
    """Diagnostic engine for arcade / fight sticks.

    Focuses on input chain speed, directional accuracy, and button combos.
    """

    input_type = InputType.FIGHT_STICK
    base_latency_ms = 4.0  # Wired fight stick baseline

    _elite_refs: dict[str, dict[str, float]] = {
        "input_chain_speed_ms": {"avg": 55.0, "top_10_pct": 38.0},
        "directional_accuracy": {"avg": 0.87, "top_10_pct": 0.95},
        "button_combo_accuracy": {"avg": 0.83, "top_10_pct": 0.94},
        "qcf_speed_ms": {"avg": 72.0, "top_10_pct": 48.0},
        "dp_input_accuracy": {"avg": 0.80, "top_10_pct": 0.93},
    }

    def analyze_events(self, events: list[InputEvent]) -> list[MechanicalLeak]:
        leaks: list[MechanicalLeak] = []

        directional = [e for e in events if e.action in ("move", "press") and any(
            d in e.input_name.lower() for d in ("up", "down", "left", "right", "qcf", "qcb", "dp", "hcf", "hcb")
        )]
        button_events = [e for e in events if e.action == "press" and not any(
            d in e.input_name.lower() for d in ("up", "down", "left", "right", "qcf", "qcb", "dp", "hcf", "hcb")
        )]
        combo_events = [e for e in events if e.action == "combo"]

        # --- Mis-chained directional inputs ---
        if directional:
            mis_chains: list[InputEvent] = []
            for i in range(1, len(directional)):
                gap = directional[i].timestamp_ms - directional[i - 1].timestamp_ms
                if gap > 120:  # >120ms between directional inputs in a motion = broken chain
                    mis_chains.append(directional[i])

            if len(mis_chains) / max(len(directional), 1) > 0.15:
                leaks.append(
                    MechanicalLeak(
                        leak_type="mis_chain",
                        description="Directional input chains broken by >120ms gaps — motion inputs not flowing",
                        frequency_per_minute=self._freq(mis_chains, events),
                        impact_rating=0.8,
                        affected_inputs=list({e.input_name for e in mis_chains}),
                        example_timestamps_ms=[e.timestamp_ms for e in mis_chains[:5]],
                    )
                )

        # --- Wasted button presses (rapid unintentional mashing) ---
        if button_events:
            mash_windows: list[InputEvent] = []
            for i in range(2, len(button_events)):
                window = button_events[i].timestamp_ms - button_events[i - 2].timestamp_ms
                if window < 40:  # 3 presses in 40ms = mashing
                    mash_windows.append(button_events[i])

            if len(mash_windows) / max(len(button_events), 1) > 0.10:
                leaks.append(
                    MechanicalLeak(
                        leak_type="wasted_input",
                        description="Button mashing detected — 3+ presses within 40ms windows",
                        frequency_per_minute=self._freq(mash_windows, events),
                        impact_rating=0.6,
                        affected_inputs=list({e.input_name for e in mash_windows}),
                        example_timestamps_ms=[e.timestamp_ms for e in mash_windows[:5]],
                    )
                )

        # --- Combo drops ---
        if combo_events:
            drops = [e for e in combo_events if e.value is not None and e.value < 0.5]
            if len(drops) / max(len(combo_events), 1) > 0.20:
                leaks.append(
                    MechanicalLeak(
                        leak_type="mis_chain",
                        description="High combo drop rate — execution breaking mid-combo",
                        frequency_per_minute=self._freq(drops, events),
                        impact_rating=0.9,
                        affected_inputs=list({e.input_name for e in drops}),
                        example_timestamps_ms=[e.timestamp_ms for e in drops[:5]],
                    )
                )

        return leaks

    def elite_benchmarks(self, skill: str) -> dict[str, float]:
        return self._elite_refs.get(skill, {"avg": 0.0, "top_10_pct": 0.0})

    def generate_drill(self, leak: MechanicalLeak) -> DrillSpec:
        drills: dict[str, DrillSpec] = {
            "mis_chain": DrillSpec(
                drill_name="Motion Input Metronome",
                target_leak="mis_chain",
                input_type=self.input_type,
                description="Execute QCF/QCB/DP motions to a metronome beat. Start at 90 BPM, increase to 140.",
                duration_minutes=15,
                difficulty="advanced",
                success_criteria="10 consecutive clean motions at 140 BPM",
                repetitions=5,
                rest_between_reps_seconds=15,
            ),
            "wasted_input": DrillSpec(
                drill_name="Single Press Discipline",
                target_leak="wasted_input",
                input_type=self.input_type,
                description="On cue, press each button exactly once. Any double-registration fails the rep.",
                duration_minutes=8,
                difficulty="intermediate",
                success_criteria="50 consecutive clean single presses",
                repetitions=4,
                rest_between_reps_seconds=10,
            ),
        }
        return drills.get(
            leak.leak_type,
            DrillSpec(
                drill_name="Fight Stick Fundamentals",
                target_leak=leak.leak_type,
                input_type=self.input_type,
                description="General fight stick warm-up: cardinal directions, diagonals, common motions, button plinks.",
                duration_minutes=12,
                difficulty="beginner",
                success_criteria="Complete full warm-up sequence",
                repetitions=2,
                rest_between_reps_seconds=10,
            ),
        )

    @staticmethod
    def _freq(subset: list[InputEvent], all_events: list[InputEvent]) -> float:
        if not all_events or len(all_events) < 2:
            return 0.0
        duration_min = (all_events[-1].timestamp_ms - all_events[0].timestamp_ms) / 60_000
        if duration_min <= 0:
            return 0.0
        return len(subset) / duration_min


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_ADAPTERS: dict[InputType, type[BaseInputAdapter]] = {
    InputType.CONTROLLER: ControllerAdapter,
    InputType.KBM: KBMAdapter,
    InputType.FIGHT_STICK: FightStickAdapter,
}


def get_adapter(input_type: InputType) -> BaseInputAdapter:
    """Return the correct adapter instance for the given input type."""
    adapter_cls = _ADAPTERS.get(input_type)
    if adapter_cls is None:
        raise ValueError(f"Unsupported input type: {input_type}")
    return adapter_cls()

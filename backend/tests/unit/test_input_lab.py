"""Unit tests for InputLab and input adapters — controller telemetry diagnostics."""

from __future__ import annotations

import pytest

from app.schemas.input_lab import (
    DrillSpec,
    EliteBenchmark,
    InputDiagnosis,
    InputEvent,
    InputProfile,
    InputType,
    MechanicalLeak,
)
from app.services.backbone.input_adapters import (
    ControllerAdapter,
    FightStickAdapter,
    KBMAdapter,
    get_adapter,
)
from app.services.backbone.input_lab import InputLab


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_events(
    count: int,
    input_name: str = "button_a",
    action: str = "press",
    duration_ms: int | None = 50,
    value: float | None = None,
    start_ms: int = 0,
    interval_ms: int = 100,
) -> list[InputEvent]:
    """Generate a list of synthetic input events."""
    return [
        InputEvent(
            timestamp_ms=start_ms + i * interval_ms,
            input_name=input_name,
            action=action,
            value=value,
            duration_ms=duration_ms,
        )
        for i in range(count)
    ]


# ---------------------------------------------------------------------------
# Adapter Factory
# ---------------------------------------------------------------------------

class TestGetAdapter:

    def test_controller(self):
        adapter = get_adapter(InputType.CONTROLLER)
        assert isinstance(adapter, ControllerAdapter)

    def test_kbm(self):
        adapter = get_adapter(InputType.KBM)
        assert isinstance(adapter, KBMAdapter)

    def test_fight_stick(self):
        adapter = get_adapter(InputType.FIGHT_STICK)
        assert isinstance(adapter, FightStickAdapter)

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            get_adapter("trackball")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ControllerAdapter
# ---------------------------------------------------------------------------

class TestControllerAdapter:

    @pytest.fixture
    def adapter(self) -> ControllerAdapter:
        return ControllerAdapter()

    def test_base_latency(self, adapter: ControllerAdapter):
        assert adapter.base_latency_ms == 8.0

    def test_no_leaks_on_clean_input(self, adapter: ControllerAdapter):
        events = _make_events(50, input_name="button_a", action="press", duration_ms=60)
        leaks = adapter.analyze_events(events)
        assert leaks == []

    def test_detects_stick_deadzone_waste(self, adapter: ControllerAdapter):
        # 80% of stick events in deadzone → should trigger
        events = (
            _make_events(80, input_name="left_stick", action="move", value=0.05, interval_ms=50)
            + _make_events(20, input_name="left_stick", action="move", value=0.8, interval_ms=50, start_ms=4000)
        )
        leaks = adapter.analyze_events(events)
        assert any(l.leak_type == "wasted_input" for l in leaks)

    def test_detects_trigger_hesitation(self, adapter: ControllerAdapter):
        events = _make_events(
            20, input_name="right_trigger", action="press", duration_ms=200, interval_ms=300
        )
        leaks = adapter.analyze_events(events)
        assert any(l.leak_type == "hesitation_window" for l in leaks)

    def test_detects_ghost_bumper(self, adapter: ControllerAdapter):
        events = _make_events(
            50, input_name="left_bumper", action="press", duration_ms=5, interval_ms=100
        )
        leaks = adapter.analyze_events(events)
        assert any(l.leak_type == "ghost_input" for l in leaks)

    def test_elite_benchmarks(self, adapter: ControllerAdapter):
        refs = adapter.elite_benchmarks("stick_efficiency")
        assert "avg" in refs
        assert "top_10_pct" in refs
        assert refs["avg"] > 0

    def test_generate_drill_returns_drill_spec(self, adapter: ControllerAdapter):
        leak = MechanicalLeak(
            leak_type="wasted_input",
            description="test",
            frequency_per_minute=5.0,
            impact_rating=0.5,
            affected_inputs=["left_stick"],
        )
        drill = adapter.generate_drill(leak)
        assert isinstance(drill, DrillSpec)
        assert drill.input_type == InputType.CONTROLLER

    def test_generate_drill_fallback(self, adapter: ControllerAdapter):
        leak = MechanicalLeak(
            leak_type="unknown_type",
            description="test",
            frequency_per_minute=1.0,
            impact_rating=0.1,
            affected_inputs=["x"],
        )
        drill = adapter.generate_drill(leak)
        assert "Warm-Up" in drill.drill_name


# ---------------------------------------------------------------------------
# KBMAdapter
# ---------------------------------------------------------------------------

class TestKBMAdapter:

    @pytest.fixture
    def adapter(self) -> KBMAdapter:
        return KBMAdapter()

    def test_base_latency(self, adapter: KBMAdapter):
        assert adapter.base_latency_ms == 3.0

    def test_detects_double_tap(self, adapter: KBMAdapter):
        # Rapid double-taps on same key
        events: list[InputEvent] = []
        for i in range(50):
            ts = i * 100
            events.append(InputEvent(timestamp_ms=ts, input_name="e", action="press", duration_ms=40))
            events.append(InputEvent(timestamp_ms=ts + 10, input_name="e", action="press", duration_ms=40))
        leaks = adapter.analyze_events(events)
        assert any(l.leak_type == "ghost_input" for l in leaks)

    def test_detects_mouse_over_correction(self, adapter: KBMAdapter):
        # Alternating positive/negative mouse values → reversals
        events: list[InputEvent] = []
        for i in range(60):
            val = 10.0 if i % 2 == 0 else -10.0
            events.append(InputEvent(
                timestamp_ms=i * 16, input_name="mouse_x", action="move", value=val
            ))
        leaks = adapter.analyze_events(events)
        assert any(l.leak_type == "over_travel" for l in leaks)

    def test_elite_benchmarks_unknown_skill(self, adapter: KBMAdapter):
        refs = adapter.elite_benchmarks("nonexistent_skill")
        assert refs == {"avg": 0.0, "top_10_pct": 0.0}


# ---------------------------------------------------------------------------
# FightStickAdapter
# ---------------------------------------------------------------------------

class TestFightStickAdapter:

    @pytest.fixture
    def adapter(self) -> FightStickAdapter:
        return FightStickAdapter()

    def test_base_latency(self, adapter: FightStickAdapter):
        assert adapter.base_latency_ms == 4.0

    def test_detects_broken_chains(self, adapter: FightStickAdapter):
        # Directional inputs with huge gaps
        events = [
            InputEvent(timestamp_ms=0, input_name="qcf_down", action="press", duration_ms=30),
            InputEvent(timestamp_ms=300, input_name="qcf_down_forward", action="press", duration_ms=30),
            InputEvent(timestamp_ms=600, input_name="qcf_forward", action="press", duration_ms=30),
        ] * 10
        # Fix timestamps to be sequential
        for i, e in enumerate(events):
            events[i] = InputEvent(
                timestamp_ms=i * 200,
                input_name=e.input_name,
                action=e.action,
                duration_ms=e.duration_ms,
            )
        leaks = adapter.analyze_events(events)
        assert any(l.leak_type == "mis_chain" for l in leaks)

    def test_detects_button_mashing(self, adapter: FightStickAdapter):
        # 3 button presses within 40ms windows
        events: list[InputEvent] = []
        for i in range(30):
            events.append(InputEvent(
                timestamp_ms=i * 10, input_name="punch", action="press", duration_ms=8
            ))
        leaks = adapter.analyze_events(events)
        assert any(l.leak_type == "wasted_input" for l in leaks)

    def test_generate_drill_for_mis_chain(self, adapter: FightStickAdapter):
        leak = MechanicalLeak(
            leak_type="mis_chain",
            description="test",
            frequency_per_minute=8.0,
            impact_rating=0.8,
            affected_inputs=["qcf"],
        )
        drill = adapter.generate_drill(leak)
        assert drill.input_type == InputType.FIGHT_STICK
        assert "Metronome" in drill.drill_name


# ---------------------------------------------------------------------------
# InputLab Engine
# ---------------------------------------------------------------------------

class TestInputLabDiagnose:

    @pytest.fixture
    def lab(self) -> InputLab:
        return InputLab()

    @pytest.mark.asyncio
    async def test_diagnose_returns_diagnosis(self, lab: InputLab):
        events = _make_events(20, input_name="button_a", action="press", duration_ms=50)
        result = await lab.diagnose_input("user1", InputType.CONTROLLER, events, "sess1")
        assert isinstance(result, InputDiagnosis)
        assert result.user_id == "user1"
        assert result.session_id == "sess1"
        assert result.total_inputs == 20

    @pytest.mark.asyncio
    async def test_diagnose_empty_telemetry(self, lab: InputLab):
        result = await lab.diagnose_input("user1", InputType.KBM, [], "sess_empty")
        assert result.total_inputs == 0
        assert result.overall_efficiency == 1.0
        assert result.leaks == []

    @pytest.mark.asyncio
    async def test_diagnose_detects_leaks(self, lab: InputLab):
        # Controller with deadzone waste
        events = _make_events(
            100, input_name="left_stick", action="move", value=0.05, interval_ms=50
        )
        result = await lab.diagnose_input("user1", InputType.CONTROLLER, events, "sess2")
        assert len(result.leaks) > 0
        assert result.wasted_inputs > 0
        assert result.overall_efficiency < 1.0


class TestInputLabDetectLeakage:

    @pytest.fixture
    def lab(self) -> InputLab:
        return InputLab()

    def test_detect_returns_leak_list(self, lab: InputLab):
        events = _make_events(10, input_name="button_a")
        result = lab.detect_mechanical_leakage(events, InputType.CONTROLLER)
        assert isinstance(result, list)

    def test_detect_with_bad_inputs(self, lab: InputLab):
        events = _make_events(
            50, input_name="left_bumper", action="press", duration_ms=5, interval_ms=100
        )
        result = lab.detect_mechanical_leakage(events, InputType.CONTROLLER)
        assert any(isinstance(l, MechanicalLeak) for l in result)


class TestInputLabCompareToElite:

    @pytest.fixture
    def lab(self) -> InputLab:
        return InputLab()

    @pytest.mark.asyncio
    async def test_compare_returns_benchmark(self, lab: InputLab):
        result = await lab.compare_to_elite("user1", InputType.CONTROLLER, "stick_efficiency")
        assert isinstance(result, EliteBenchmark)
        assert result.user_id == "user1"
        assert result.input_type == InputType.CONTROLLER

    @pytest.mark.asyncio
    async def test_compare_unknown_skill(self, lab: InputLab):
        result = await lab.compare_to_elite("user1", InputType.KBM, "nonexistent")
        assert isinstance(result, EliteBenchmark)
        assert result.elite_avg == 0.0


class TestInputLabGenerateDrill:

    @pytest.fixture
    def lab(self) -> InputLab:
        return InputLab()

    def test_generates_drill_for_leak(self, lab: InputLab):
        leak = MechanicalLeak(
            leak_type="wasted_input",
            description="test",
            frequency_per_minute=5.0,
            impact_rating=0.5,
            affected_inputs=["left_stick"],
        )
        drill = lab.generate_correction_drill(leak, InputType.CONTROLLER)
        assert isinstance(drill, DrillSpec)
        assert drill.target_leak == "wasted_input"


class TestInputLabProfile:

    @pytest.fixture
    def lab(self) -> InputLab:
        return InputLab()

    @pytest.mark.asyncio
    async def test_empty_history_profile(self, lab: InputLab):
        result = await lab.get_input_profile("user1", InputType.CONTROLLER)
        assert isinstance(result, InputProfile)
        assert result.total_sessions_analyzed == 0
        assert result.avg_efficiency == 0.0


# ---------------------------------------------------------------------------
# InputLab helper methods
# ---------------------------------------------------------------------------

class TestInputLabHelpers:

    def test_count_wasted_no_leaks(self):
        events = _make_events(10)
        assert InputLab._count_wasted([], events) == 0

    def test_count_wasted_with_leaks(self):
        events = _make_events(100, interval_ms=100)  # 10 seconds of data
        leak = MechanicalLeak(
            leak_type="wasted_input",
            description="test",
            frequency_per_minute=60.0,  # 1 per second → ~10 in 10s
            impact_rating=0.5,
            affected_inputs=["x"],
        )
        wasted = InputLab._count_wasted([leak], events)
        assert wasted > 0
        assert wasted <= len(events)

    def test_build_summary_elite(self):
        summary = InputLab._build_summary(InputType.CONTROLLER, 0.98, [])
        assert "elite" in summary.lower()

    def test_build_summary_needs_work(self):
        leak = MechanicalLeak(
            leak_type="wasted_input",
            description="test",
            frequency_per_minute=10.0,
            impact_rating=0.8,
            affected_inputs=["x"],
        )
        summary = InputLab._build_summary(InputType.KBM, 0.55, [leak])
        assert "need" in summary.lower() or "work" in summary.lower()

    def test_rate_percentile_above_elite(self):
        pct = InputLab._rate_percentile(0.98, 0.90, 0.95)
        assert pct > 95

    def test_rate_percentile_below_average(self):
        pct = InputLab._rate_percentile(0.30, 0.90, 0.95)
        assert pct < 50

    def test_timing_percentile_faster_than_elite(self):
        pct = InputLab._timing_percentile(20.0, 45.0, 32.0)
        assert pct > 95

    def test_timing_percentile_slower_than_average(self):
        pct = InputLab._timing_percentile(80.0, 45.0, 32.0)
        assert pct < 50

    def test_benchmark_verdict_elite(self):
        assert InputLab._benchmark_verdict(95.0) == "elite"

    def test_benchmark_verdict_needs_work(self):
        assert InputLab._benchmark_verdict(10.0) == "needs-work"

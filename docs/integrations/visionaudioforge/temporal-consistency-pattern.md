# Temporal-Consistency Pattern — Categorical-vs-Numeric Smoothing

- **Status:** v1 — established during M5c sub-task 6 (2026-06-30).
- **Engine:** `services/visionaudioforge/app/core/temporal.py` (`TemporalSmoother`) — title-agnostic, in core.
- **Config:** each adapter declares a `smoothing_schema` class attribute (Forge Rule 5: adapters add config, not core code).
- **Audience:** every future title adapter with per-frame classifier/OCR outputs — CFB 26, NBA 2K26, EA FC 26, MLB 26, …
- **Cross-references:** [ADR 0013](../../adr/0013-hud-calibration-recurring-maintenance.md), [ADR 0014](../../adr/0014-ocr-overlay-over-cnn-for-formation-signals.md), [HUD calibration methodology](madden26-hud-calibration-methodology.md), [M5c plan](../../phase-completions/0-vaf-m5c-plan.md) sub-tasks 6 / 6.5.

## Why

Per-frame signals — OCR reads, classifier/overlay labels — carry single-frame errors. A field position misread once as "+47" among six "+41" frames, a formation OCR'd once as "Doubies", a clock digit flipped 1↔7. The value is stable over the ~seconds it is on screen, so **a rolling window of recent frames outvotes the stray frame.** The engine is title-agnostic; only the per-field schema is per-title.

## The categorical-vs-numeric distinction (the core pattern)

Two value families, aggregated differently across the window. **This distinction is the reusable decision every adapter makes per field:**

| Family | Aggregation | Use for | Examples |
| --- | --- | --- | --- |
| **categorical** | **mode** (majority vote) | discrete labels prone to single-frame errors | formation, possession, down |
| **numeric** | **median** | numeric readings with a bounded change rate | field_position, distance, score, play_clock |

- **Categorical → mode.** A label is right or wrong; averaging is meaningless. The most-frequent value in the window wins; a lone misread is outvoted. (Madden formation, CFB 26 formation, NBA 2K26 play concept, EA FC 26 tactical shape all use this.)
- **Numeric → median.** The median is robust to a single outlier misread (unlike the mean) and, unlike mode, tolerates the value genuinely drifting by ±1. The smoother returns the buffered value nearest the median so original formatting is preserved (`"+41"`, `"OPP_22"`).
- **`string_clock`** is a categorical-style mode over `"M:SS"` strings — a monotonically-decreasing value where the mode trails by ≤1 frame (≈16–33 ms at capture fps, below human perception and far under the >2 s end-to-end budget). This is why smoothing the clock is safe despite it changing every second.

Per-field config: `window` (max frames retained) and `min_window` (frames required before the smoother emits a vote rather than passing the raw value through). Fast-changing fields (score, play_clock) use small windows (3); slower/stable fields (field_position) use larger (7).

## Context-switch reset (shared by both families)

Every field carries a **context tag**. When it changes, that field's window is **cleared** — values are never smoothed across a context boundary. In Madden 26 the HUD flips between two contexts:

- `live_gameplay` — scorebug + down/distance visible → the OCR fields are smoothed here.
- `play_call` — the play-call overlay is up (formation name readable, scorebug hidden) → the formation is smoothed here.

The formation window **resets on the `play_call → live_gameplay` switch**, so two consecutive play-call screens never mode-vote across each other (screen A = "Trips", screen B = "Bunch" must not blend). Sub-task 6.5 validates this reset explicitly. The reset is the mechanism that makes per-context signals composable in one smoother.

## When NOT to smooth

- **One-shot events** — a `SCORE_CHANGE` timestamp, a snap detection. Smoothing would delay or blur them. Smooth the *state* fields feeding an event, not the event's trigger moment.
- **Fields that legitimately change every frame with no stable window** — none in the current schema, but a play-clock at 60 fps counting down would need window ≤2 to avoid lag.

## Wiring a new adapter

1. Declare a `smoothing_schema` class attribute: `{field: {"kind": ..., "window": N, "min_window": M}}`.
2. In the state assembler, get the per-session `TemporalSmoother` from `session.adapter_state`, tag the current context, and call `apply_schema(smoother, raw_values, schema_subset, context)` on the context-relevant fields.
3. Reset the relevant field(s) on context switches (`smoother.reset(field)`).

No core change. The engine and this pattern transfer unchanged; only the schema and the context definitions are per-title.

# Temporal-Consistency Pattern — Categorical-vs-Numeric Smoothing + Sampled OCR

- **Status:** v2 — smoothing established in M5c sub-task 6; sampled-OCR cadence + context-detection patterns added in sub-task 7.5 (2026-06-30).
- **Engine:** `services/visionaudioforge/app/core/temporal.py` (`TemporalSmoother`) + `app/core/ocr_cadence.py` (`OcrCadenceScheduler`) — both title-agnostic, in core.
- **Config:** each adapter declares `smoothing_schema` and `ocr_cadence_schema` class attributes (Forge Rule 5: adapters add config, not core code).
- **Audience:** every future title adapter with per-frame classifier/OCR outputs — CFB 26, NBA 2K26, EA FC 26, MLB 26, …
- **Cross-references:** [ADR 0013](../../adr/0013-hud-calibration-recurring-maintenance.md), [ADR 0014](../../adr/0014-ocr-overlay-over-cnn-for-formation-signals.md), [ADR 0015](../../adr/0015-tiered-budget-and-sampled-ocr-cadence.md), [HUD calibration methodology](madden26-hud-calibration-methodology.md), [M5c plan](../../phase-completions/0-vaf-m5c-plan.md) sub-tasks 6 / 6.5 / 7.5.

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

## Smoothing across *sampled* reads (sub-task 7.5)

CPU OCR is too slow to run every field every frame (ADR 0015), so fields are read on a **cadence** — the game clock every ~1 s, down/distance a few times a second, teams once per session. This changes what the smoothing window *means*, and the change is the pattern:

- **Smooth only the fields freshly read this frame; carry the last smoothed value forward for the rest.** A field that was not sampled this frame is *not* fed to the smoother — otherwise the window fills with duplicated carried values and a genuinely new read is out-voted by its own stale copies.
- **The window therefore holds the last K *sampled reads*, not the last K frames.** A `window: 3` on a field read every 12 frames spans ~36 frames of wall-clock but only 3 real observations. Tune windows in *reads*, not frames: boundary-ish fields use small windows (a fresh per-play read should win quickly).
- **A null read is not an observation.** If OCR can't read a field this frame (occluded, between plays), keep the last good cached value — do not clobber it with `None`, and do not count it as a fresh read.
- **Emit on fresh reads only.** A frame that read nothing (pure hot-path frame) emits no SNAPSHOT — this both avoids unchanged-state spam and keeps the event rate tied to the sampling cadence.

This is why sampling and smoothing compose cleanly rather than fight: the smoother was always sample-based (it buffers values, not frames), so feeding it only fresh reads is the natural fit. Generalises to any adapter doing sampled OCR — the schema changes, the pattern does not.

## Prefer periodic reads over trigger-based reads when the trigger is a *proxy*

A tempting cadence is "read field X only when event Y fires" (read down/distance only at a play boundary). It's correct **only when the trigger is reliable.** In Phase 0 the play-boundary signal is a cheap frame-diff *proxy* (the real snap detector is later work) that sometimes fires on a transition frame where the HUD is redrawing — so the single triggered read lands on a null/garbage frame and caches null until the next trigger (a whole play of dark state).

**Rule: when the trigger is a heuristic proxy, prefer a periodic `every_n` read over a trigger-gated single read.** A periodic read is self-healing — a bad read is retried a fraction of a second later — at the cost of a little extra OCR (still within the OCR-tier budget). Keep the proxy for *coarse* roles it's good enough for (here: marking the play-epoch boundary that resets smoothing context), not for the *precise* moment of a single critical read. When a *reliable* trigger arrives (a real snap detector), revisit — that's a per-adapter decision, documented in that adapter's milestone, not baked in globally.

## Context detection for overlay-vs-gameplay HUDs

Sports titles alternate between **gameplay** and a **menu-style overlay** (play-call, tactics, pause, substitutions). The adapter needs to know which is on screen to pick the right OCR (and the right smoothing context) — and it must decide *cheaply*, on the hot path, without OCR.

**`dark_frac` is the first signal to try, portfolio-wide.** The near-universal UI convention is that a menu-style overlay **dims the underlying field** — a translucent scrim behind the menu. The fraction of the frame below a low luma threshold (`dark_frac`) jumps on the overlay and is a **title-UI constant**, not a game-mode-dependent quantity. In Madden 26 calibration it separated play-call from live with 0 false-negatives where a scoreboard-brightness feature failed (that one was bright in one capture mode, dark in another — mode-dependent, wrong). Expect the dimming convention to hold across NBA 2K, EA FC, NHL, MLB The Show; try `dark_frac` (optionally AND a lit-banner region check) before anything heavier like template-match.

**Pair the cheap signal with a semantic guard — defense-in-depth (canonical).** The hot-path context detector is fast and therefore fallible on transition frames. Do **not** let a downstream reader trust it blindly: the reader must carry its own semantic sanity check. In Madden, `read_formation_name` only accepts a read that matches the `"<name> - N Plays"` pattern, so a context-detector false-positive on a transition frame yields a null formation, not a spurious `FORMATION_LOCKED`. **Fast cheap signal on the hot path + semantic guard at the reader layer** is the pattern every adapter should follow; it also mirrors the title-detector's cheap-heuristic-then-verify shape (ADR 0007).

## Wiring a new adapter

1. Declare a `smoothing_schema` class attribute: `{field: {"kind": ..., "window": N, "min_window": M}}`.
2. In the state assembler, get the per-session `TemporalSmoother` from `session.adapter_state`, tag the current context, and call `apply_schema(smoother, raw_values, schema_subset, context)` on the context-relevant fields.
3. Reset the relevant field(s) on context switches (`smoother.reset(field)`).

No core change. The engine and this pattern transfer unchanged; only the schema and the context definitions are per-title.

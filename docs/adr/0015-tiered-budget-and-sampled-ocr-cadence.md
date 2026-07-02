# ADR 0015 — Tiered Per-Frame Budget + Sampled-OCR Cadence

- **Status:** Accepted
- **Date:** 2026-06-30
- **Reference:** [CLAUDE.md](../../CLAUDE.md) — project development context. Aligns with the Forge "adapters extended without core changes" principle (Rule 5): the cadence *engine* and the tier-aware gate live in `core/`; the per-field cadence and budget values live on the adapter. (The canonical Forge-rules doc `FORGE_ARCHITECTURE_PATTERN.md` is referenced repo-wide but not yet committed — tracked debt, see ADR 0013 followups.)
- **Supersedes / amends:** [ADR 0006](0006-tiered-per-frame-budget.md) — 0006's single `max_processing_ms` per adapter version is replaced by a two-tier budget (hot path + sampled OCR). The version-scaling idea in 0006 is retained; it now applies to the *hot-path* tier.
- **Establishing case:** M5c sub-task 7.5 (OCR-cadence reform), triggered by the Phase 0 final-acceptance failure (sub-task 7: criteria 4 & 8).
- **Related:** [ADR 0014](0014-ocr-overlay-over-cnn-for-formation-signals.md) (OCR-of-overlay — the pivot that created the throughput problem this ADR resolves), [ADR 0007](0007-title-detection-fallback.md) (cheap heuristic + guard precedent), [temporal-consistency pattern](../integrations/visionaudioforge/temporal-consistency-pattern.md) (sampled-read smoothing).

## Context

ADR 0006 set the per-frame adapter budget at a flat **80 ms** (v0.1), premised on a cost model of *fast CNN inference + lightweight extraction*. The ADR 0014 pivot replaced the CNN with **OCR-of-overlay** (EasyOCR on CPU), which has a completely different cost profile — **~65 ms per text crop**. The Phase 0 final acceptance (sub-task 7) measured the consequence on real footage:

- Adapter **p50 ≈ 1000 ms / p95 ≈ 1032 ms** per frame — the adapter ran **two** full EasyOCR passes every frame (`read_frame` scorebug ≈ 656 ms + `is_play_call_screen` ≈ 341 ms).
- The dispatcher's flat 80 ms gate then **dropped 100 % of frames → zero events emitted** end-to-end. The perception pipeline produced nothing on real gameplay.

The key realisation: **a single CPU OCR crop already blows an 80 ms per-frame budget.** No amount of cadence-thinning makes an individual OCR frame fit 80 ms, because the gate is *per frame*. The 80 ms number is right for a hot path that does no OCR; it is the wrong instrument for OCR frames. OCR must be **decoupled from the real-time hot path** — sampled on a cadence, with its own budget, and exempt from the hot-path drop.

## Decision

### 1. Two-tier per-frame budget

| Tier | Runs | Budget | Measured (real footage, warm) |
|---|---|---|---|
| **Hot path** — integrity gate, cheap context detection, frame-diff, snap | **every frame** | **80 ms** (v0.1; scales with version per ADR 0006) | p95 **15 ms** |
| **OCR tier** — a sampled OCR read (scorebug fields or formation name) | **on cadence only** | **500 ms** | p95 **172 ms** |

The dispatcher gate is **tier-aware** (`app/core/dispatcher.py`): the adapter signals the frame's tier (`session.adapter_state["_last_tier"]`); a hot-path frame over 80 ms is a genuine "behind real time" breach and drops; a scheduled OCR-tier frame is evaluated against the 500 ms budget and is **not** dropped for exceeding the hot-path budget. Adapters declare `max_processing_ms` (hot) and `max_ocr_tier_ms` (OCR); the dispatcher falls back to `max_processing_ms` for adapters that predate this ADR. Per-tier latency is reported separately.

### 2. Sampled-OCR cadence

HUD fields change at different natural rates; OCR only runs for a field when it is *due*. A title-agnostic scheduler (`app/core/ocr_cadence.py`) is driven by a per-adapter `ocr_cadence_schema`. Cadence kinds: `once_per_session`, `every_n` (with phase offset), `on_play_boundary`, `on_play_call`. Each group declares the HUD **context** it belongs to; the frame's context comes from the cheap `ContextDetector` (see §3), not from OCR.

**Madden 26 v0.1 cadence:**

| Group | Fields | Cadence | Why |
|---|---|---|---|
| team_abbrevs | team_home/away_abbr | `once_per_session` | constant for a game |
| down_distance | down, distance, field_position | `every_n` (12, ≈0.4 s @30 fps) | change once per play — see deviation below |
| clock | clock | `every_n` (10) | ~1 Hz game clock |
| score_quarter | score_home/away, quarter | `every_n` (40) | change rarely |
| formation | offensive_formation | `on_play_call` (≤5 reads/screen) | mode-vote the play-call banner, then idle |

Result on real footage: **78 % of frames do zero OCR** (hot tier); events flow at ~2/s (a SNAPSHOT per sampled live read + FORMATION_LOCKED per play-call screen). `play_clock` is omitted from the v0.1 cadence (not in the Phase-0 payload) and returns with the M5b snap detector.

### 3. Cheap context detection on the hot path + defense-in-depth

The second per-frame OCR pass (`is_play_call_screen`, ~341 ms) is replaced by a **non-OCR `ContextDetector`** (~0.7 ms) that decides play-call-vs-live from two grayscale features: the formation-banner luma and whole-frame **`dark_frac`** (the play-call menu dims the field — a title-UI constant). Calibrated to **0 false-negatives** (no play-call screen missed) over 174 real frames.

This establishes a **defense-in-depth** contract, canonical for future adapters: **a fast cheap signal gates the hot path, and a semantic guard at the reader layer is the backstop.** Here, even if the context detector false-positives on a transition frame, `read_formation_name`'s `"N Plays"` OCR guard returns null, so no spurious `FORMATION_LOCKED` can fire. A reader must never blindly trust the upstream cheap signal.

### 4. Deviation — `down_distance` uses `every_n`, not `on_play_boundary`

The plan specified `on_play_boundary` for down/distance. **That assumed a working snap detector.** The real snap detector is M5b (later work); the Phase 0 boundary trigger is a cheap frame-diff *proxy* that sometimes fires on transition frames where the HUD is redrawing or mid-fade. A single boundary-triggered read that lands on such a frame gets null and **caches null for the whole play**, manifesting as dark down/distance state (observed during 7.5 integration).

**`every_n` (12 ≈ ~0.4 s at 30 fps) is robust to imprecise boundary detection: a missed read is retried naturally.** The boundary proxy is retained but restricted to the **play-epoch reset** role (marking smoothing-context boundaries so a new play's read doesn't mode-vote against the prior play's), **not** the OCR-trigger role. This is the correct trade-off: small additional OCR cost (down/distance runs ~2.5×/s instead of ~1×/play) for robustness against an imperfect proxy — still well within the OCR-tier budget (172 ms p95 ≪ 500 ms), 78 % of frames doing zero OCR.

**Revisit at M5b:** with a real snap detector, either keep the periodic reads as defense-in-depth, or switch back to `on_play_boundary` if the real detector proves reliable enough. That decision belongs in M5b's ADR, not this one.

## Consequences

- Phase 0 acceptance criteria 4 & 8 are re-stated against the tiered model: **hot-path p95 ≤ 80 ms** (with headroom) **and OCR-tier p95 ≤ 500 ms** (C4); **integrated e2e p95 < 500 ms** (C8). A new **events-emitted > 0 at a sane rate** guard is added to catch the zero-output failure mode as a first-class gate.
- `read_frame` (the full-scorebug read) is **untouched** — it remains the validated artifact the v2.1.0 OCR regression baseline reproduces against. The cadence path uses a new `read_fields` partial read that mirrors it exactly (verified byte-identical).
- The smoother interacts with sampling via the **"smoothing across sampled reads"** pattern (only fresh reads are smoothed; the window is the last K *sampled reads*, not K frames) — documented in the [temporal-consistency pattern](../integrations/visionaudioforge/temporal-consistency-pattern.md).
- Cold-start: the first OCR frame pays EasyOCR's one-time model load (~2.8 s). Steady-state p95 is unaffected; harnesses warm the reader before measuring.

## Followups

- **M5b:** revisit the `down_distance` cadence once the real snap detector lands (§4). Re-add `play_clock` to the cadence for snap detection then.
- **CFB 26 / other titles:** the cadence schema + tiered budget transfer unchanged; only the per-field cadences and context features are per-title. `dark_frac` is the first context feature to try (menu screens dim the field across NBA 2K / EA FC / NHL / MLB The Show — see methodology doc).
- If a future title's OCR-tier p95 approaches 500 ms, either thin its cadence or move OCR to a background worker (fully async, off the dispatch thread) — the next escalation beyond this ADR's synchronous-but-sampled model.

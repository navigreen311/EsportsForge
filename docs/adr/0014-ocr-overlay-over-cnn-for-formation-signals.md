# ADR 0014 — Prefer OCR-of-Overlay Over CNN-from-Pixels for Explicit Game-UI Signals

- **Status:** Accepted
- **Date:** 2026-06-30
- **Reference:** [CLAUDE.md](../../CLAUDE.md) — project development context. Aligns with the Forge "adapters extended without core changes" principle (Rule 5): the formation detector + its calibration live entirely in the Madden adapter; core is untouched. (The canonical Forge-rules doc `FORGE_ARCHITECTURE_PATTERN.md` is referenced repo-wide but not yet committed — tracked debt, see ADR 0013 followups.)
- **Establishing case:** M5c sub-task 4 (Madden 26 offensive-formation detector).
- **Related:** [ADR 0013](0013-hud-calibration-recurring-maintenance.md) (HUD re-calibration), [HUD calibration methodology](../integrations/visionaudioforge/madden26-hud-calibration-methodology.md), [training-data labeling protocol](../integrations/visionaudioforge/training-data-labeling-protocol.md), [M5c plan](../phase-completions/0-vaf-m5c-plan.md) sub-task 4.

## Context

M5c sub-task 4 set out to classify the offensive formation (top-8 for v0.1) with a MobileNetV3-Small CNN over the gameplay frame — the plan's assumption was pixel-based classification of the on-field player layout.

That assumption was tested to exhaustion and failed:

- **12 training runs across the full technical ladder:** regularization (frozen-head linear probe, weight decay, strong augmentation), capacity (MobileNetV3-Small vs Large), input size (224 vs 192), learning rate, class-weighted vs unweighted loss, label-quality filtering, and two tighter-crop re-extractions (wide-band and square-core).
- **Single-model ceiling ≈ 0.22 macro-F1** vs the 0.85 target. Per-cluster: the well-supported formations (wing/i_form/trips/empty/bunch) topped out ~0.33 macro-F1; the rare, data-starved classes (ace/pistol/doubles, test support 3–20) were ~0.00.
- **Diagnosis (evidence, not assertion):** the failure is *not* overfitting alone (regularization roughly doubled test F1 but plateaued), *not* label noise (high-quality-only training did not help), and *not* zero-signal (some classes reached 0.5–0.8 in individual configs). It is **insufficient pixel detail**: Madden's elevated, ball-following gameplay camera renders the 11 offensive players as ~5–15 px of overlapping shapes after crop+resize, which is not enough to resolve QB depth (shotgun/pistol/under-center) or WR-count-per-side (trips/bunch/doubles/empty) — the exact distinctions the taxonomy is built on. The same limitation blocked human/agent labeling of the same frames.

Meanwhile, the game **already displays the formation as explicit text** on its play-call / formation-select overlay ("Trips TE Offset - 12 Plays"). An OCR feasibility check read this reliably: **100% (40/40) on the 8 canonical practice clips (avg conf 0.82), production-confirmed on a human exhibition clip.**

## Decision

**For any adapter classifier sub-task, first ask: "is this signal available as explicit text on the game UI?" If yes, prefer OCR-of-overlay over CNN-from-pixels. Reserve pixel-based CNNs for signals the UI does not surface as text.**

Concretely for Madden 26 formation detection (v0.1):

1. The formation is read from the **play-call overlay** via the shared OCR pipeline (`hud_regions.json` v2.2.0 `play_call.formation_name` region), not a CNN. The full Madden name ("Trips TE Offset") is the primary label; a canonical-8 family tag is derived via keyword mapping.
2. The CNN training pipeline (`services/visionaudioforge/training/`) is **retained but not shipped** — it is the evidence artifact and a reusable harness should a title ever lack a text signal and warrant a CNN with adequate capture.
3. **Capture mode is now a first-class requirement:** OCR-of-overlay needs a capture that *includes the play-call screen*. CPU-vs-CPU captures live gameplay but the CPU picks plays off-screen, so the overlay never appears — see the [labeling protocol](../integrations/visionaudioforge/training-data-labeling-protocol.md). Practice play-select and human-played gameplay show it.

## Consequences

- **v0.1 formation acceptance criterion changes** from CNN macro-F1 ≥ 0.85 to **OCR formation-name success ≥ 80% on the canonical 8 across production conditions** (met: 100% practice + production-confirmed). Sub-task 5 evaluation moves from CNN metrics (confusion matrix, latency of an ONNX model) to OCR metrics (per-formation read rate, confidence, state-detector gating).
- **`hud_regions.json` becomes multi-context (v2.2.0):** `live_gameplay` (v2.1.0 scorebug/down-distance) vs `play_call` (the overlay). This overlay-vs-gameplay context split is the reusable shape for future title adapters.
- **Temporal smoothing (sub-task 6) applies unchanged:** formation is a categorical field, stable within a play-call screen; the title-agnostic smoother mode-votes away single-frame OCR misreads.
- **Throughput cost is resolved by [ADR 0015](0015-tiered-budget-and-sampled-ocr-cadence.md):** OCR-of-overlay is far slower per frame than the CNN it replaced (CPU EasyOCR ~65 ms/crop), which broke the flat 80 ms budget and dropped 100 % of frames at Phase 0 acceptance. ADR 0015 introduces the tiered budget + sampled-OCR cadence + cheap non-OCR context detection that make the pivot viable in real time.
- The gameplay-camera CNN limitation is a **general finding**: any fine on-field geometry (defensive front, coverage shells) will face the same pixel-detail wall from the broadcast camera. Prefer the UI text signal where the game exposes one.

## Followups

- **v0.3 (24-formation taxonomy):** add left-panel family disambiguation — single-word names ("Pro", "Strong") are unique within the canonical 8 but ambiguous across the full set.
- **Capture-mode note in the local-capture protocol:** formation training/detection requires play-call-screen capture, not CPU-vs-CPU.
- If a future title lacks any text formation signal, revisit the retained CNN harness *with a capture mode that provides adequate player resolution* (e.g. an all-22 / coaches'-film camera) before concluding infeasibility — do not generalize this ADR to "CNN never works," only "CNN-from-broadcast-camera is insufficient for fine on-field geometry at this data scale."

# ADR 0006 — Tiered Per-Frame Adapter Budget

- **Status:** Accepted
- **Date:** 2026-05-06
- **Reference:** [FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md) — Rule 5 (adapters added without core changes — adapter version drives budget; the core enforces what the adapter declares).
- **Modifies:** [specs/02-visionaudioforge-core.md §1 "Adapter contract"](../specs/02-visionaudioforge-core.md), [specs/02-visionaudioforge-core.md §4 "Performance budget per frame"](../specs/02-visionaudioforge-core.md).

## Context

Spec #2 sets the per-frame adapter latency budget at **80 ms**. The Madden 26 adapter v0.1 (offensive formation only) fits in ~58 ms by the spec's own breakdown, so 80 ms is comfortable. However, when v0.3 adds defensive front + post-snap coverage detection (~25 ms additional inference), the total reaches **~88 ms** — over the budget.

The spec acknowledged this and proposed mitigations (run formation detector every other frame, drop CNN input from 224×224 to 192×192). But fixing the 80 ms ceiling and forcing every future adapter feature into mitigation-mode misses the real shape of the problem: features ship over time, complexity increases, and the budget should grow with documented adapter versions rather than be fought against.

## Decision

**Adopt a tiered per-frame budget that scales with adapter version:**

| Adapter version | Budget | Rationale |
|---|---|---|
| v0.1 (offensive formation only) | **80 ms** | Spec's measured ~58 ms with comfortable headroom. |
| v0.2 (+ pre-snap defensive front) | **100 ms** | Adds ~15 ms inference. |
| v0.3 (+ post-snap coverage detection) | **120 ms** | Adds another ~25 ms inference. |
| v0.4+ (future features) | declared per release | Bump the constant when features ship. |

The `max_processing_ms` field on the `TitleAdapter` contract becomes the source of truth — set per adapter, per version. The core enforces what the adapter declares; deploying an adapter with a higher budget is a deploy-level decision, not a code-level surprise.

**Document the budget tiering explicitly in the adapter README so future authors know the budget grows with feature scope, not by force.**

## Consequences

- The 80 ms constant in Spec #2 §4 is no longer fixed — it's the v0.1 value. v0.3 ships with 120 ms; future adapters declare their own.
- 12 fps capture cadence × 120 ms processing = adapter still keeps up with real time (8.3 fps inference vs 12 fps capture; falling behind by 30%, but cache + de-duplication absorb this).
- 24 fps adaptive ramp × 120 ms processing = adapter falls behind during motion bursts; queue grows transiently. Acceptable if it drains within 1–2 s.
- Adapter v0.3 testing must validate the 120 ms ceiling with real-world Madden gameplay traces, not just synthetic frames.

## Notes / followups

- If v0.3 testing shows the 120 ms ceiling breached at p95 on real captures, fall back to the spec's mitigations (every-other-frame inference for defense, smaller CNN input). The tiered budget gives explicit head-room before reaching for mitigations.
- Future adapters for higher-fps sports (Warzone, NBA — see [ADR 0005](0005-per-adapter-frame-rate-override.md)) may need *lower* budgets to keep up with their FPS cadence. The same tiered mechanism handles both directions.

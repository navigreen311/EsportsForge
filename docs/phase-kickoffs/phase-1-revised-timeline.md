# Phase 1 — Revised Calendar (1a, 1b, 1c, 1.1)

- **Status:** Working timeline. Phase 1 calendar starts **only after** Phase 0 acceptance returns.
- **Date:** 2026-05-07 (revised after pre-merge review of PR #62 / PR #63)
- **Source:** Pre-merge review surfaced that Phase 0 is not yet complete — 5 of 8 acceptance criteria fail against real Madden 26 footage. Work that this doc previously mis-classified as Phase 1 prerequisites (M4.5, M5c, OCR cadence reform) is in fact Phase 0 remainder. Phase 1 starts after that closes.
- **Reference:** [Phase 0 status](../phase-completions/0-vaf-foundation.md), [Phase 0 remaining milestones](../phase-completions/0-vaf-remaining-milestones.md), [docs/specs/03-mock-removal-and-page-wiring.md §3](../specs/03-mock-removal-and-page-wiring.md), [ADR 0010](../adr/0010-phase-1c-gated-on-adapter-v0-3.md), [real-footage validation](../phase-completions/0-real-footage-validation.md).

## Why the original timeline was wrong (and the earlier revision was also wrong)

The Phase 0 close estimate put Phase 1 at **~6 weeks**. That number assumed the Phase 0 stub work (formation = constant, HUD bboxes correct, OCR budget met) was real enough to build on. Real-footage validation showed it wasn't.

An **earlier revision** of this doc tried to fix the estimate by reframing M4.5 + M5c + OCR cadence reform as "Phase 1a prerequisites." That framing was also wrong. Those items aren't prerequisites for Phase 1a — they're the **rest of Phase 0**. Calling them Phase 1 prerequisites would have let Phase 0 quietly merge without meeting its own acceptance criteria, and the discipline of "phase X must close cleanly before phase X+1 starts" would erode.

This revision corrects both. Phase 0 has remaining work; that work is **Phase 0**. Phase 1's calendar starts when Phase 0's 8 acceptance criteria pass on real footage.

## Phase 0 remainder (not part of this calendar; included for sequencing only)

Per [0-vaf-remaining-milestones.md](../phase-completions/0-vaf-remaining-milestones.md):

| Milestone | Estimate |
|---|---|
| M4.5 — HUD region calibration | 3 days |
| M5c — Real formation classifier training | 3–5 days |
| OCR cadence reform | 1 day |
| Real-footage validation re-run | 0.5 day |
| Phase 0 status doc → completion sign-off | 0.5 day |

**Phase 0 remainder total: 8–10 working days.** PR #62 + PR #63 stay open across this window.

Phase 1a Day 0 cannot start before this completes.

## Phase 1 calendar (starts the day after Phase 0 acceptance returns)

| Phase | Calendar | Build days | Observation days | Notes |
|---|---|---|---|---|
| **Phase 1a — Drill Lab cutover** | ~2 weeks | 5 days | 7 days | Build sequence as originally specified: events WS endpoint, useVisionEvents hook, Drill Lab page rewire, Settings flag exposure, e2e manual test, staff-cohort flip. Observation window 7 days. **No M4.5/M5c/OCR work — those closed in Phase 0.** |
| **Phase 1b — SimLab + Gameplan cutover** | ~2 weeks | 7 days | 7 days | Re-uses Phase 1a's `useVisionEvents` hook + event WS endpoint. SimLab subscribes to `FORMATION_LOCKED`; Gameplan subscribes to `COVERAGE_LOCKED` (won't fire until v0.3 — graceful empty per ADR 0010). |
| **Phase 1.1 — Madden v0.2 + v0.3** | ~2 weeks | 10 days | 0 days | v0.2 = pre-snap defensive front (3 days). v0.3 = post-snap coverage classifier (5 days). Plus 2 days of integration + adapter macro-F1 validation. Per ADR 0010 this lands **between** 1b and 1c. |
| **Phase 1c — Arsenal + War Room cutover** | ~2 weeks | 7 days | 7 days | Per ADR 0010, gated on v0.3 production-stable for 7 days. 1c-blocking webhook alarm (per ADR 0003) must not have fired during 1a or 1b. |
| **Buffer** | 1–2 weeks | — | — | Empirically every phase takes 10–20% longer than estimated. Reserve. |

**Phase 1 total: 8 weeks (best case) to 10 weeks (with buffer).**

Combined with Phase 0 remainder: **~10–12 weeks calendar from today (2026-05-07)** to Phase 1 close.

## Why this is shorter than the previous revision suggested

The previous revision claimed 9–11 weeks for Phase 1 alone, by including M4.5/M5c/OCR within Phase 1a. The honest accounting:

- Those items are Phase 0 work (they close Phase 0's acceptance criteria), so they belong in Phase 0's calendar, not Phase 1's.
- Phase 1a's actual build sequence is the 5-day cutover work originally specified.

The total time-to-Phase-1-close is roughly the same as the previous revision (10–12 weeks vs. 9–11 weeks); only the **labeling** changes. The labeling matters because it preserves "Phase 0 must close cleanly before Phase 1 starts."

## What's parallelisable (unchanged from earlier revision)

1. **Inside Phase 0 remainder, M5c training (Days 1–5) overlaps with M4.5 day 3.** The classifier training can begin once Day 1 labels exist; the day-3 calibration validation runs in parallel. Saves ~1–2 days if both can run concurrently. Requires the same engineer to drive both, which is fine — labeling and training each have idle stretches.

2. **Inside Phase 1, M5 v0.2 (defensive front, Phase 1.1) can start during Phase 1b's observation window.** v0.2 doesn't block 1b's SimLab cutover. Saves ~3 days if calendar is tight.

3. **The Phase 1b cutover code can be written during Phase 1a's observation window** if a second engineer is available. Saves ~1 week.

With one engineer end-to-end, the timeline is sequential. With two, the optimistic end of the range is reachable.

## Risks that could blow the timeline

| Risk | Where it lives | Mitigation |
|---|---|---|
| **OCR cadence reform doesn't drop p95 under 80 ms.** | Phase 0 remainder, Milestone 3 | Fallback to ONNX digit-classifier (+2–3 days). Documented in milestone breakdown. |
| **M5c classifier doesn't hit macro-F1 ≥ 0.85.** | Phase 0 remainder, Milestone 2 | Day-5 buffer absorbs first re-train. If second re-train fails, expand training set; +2 days. |
| **HUD bbox calibration disagrees across frame types (replay vs live).** | Phase 0 remainder, Milestone 1 | Calibrate against live frame only; treat replay HUD as Phase 2 scope. |
| **Webhook alarm fires during Phase 1a or 1b.** | Phase 1 | Phase 1c blocked until Redis Streams ships (ADR 0003). +5–7 days. CloudWatch alarms deploy to staging on Phase 1a Day 0. |
| **Capture agent stability on real player machines.** | Phase 1a | Phase 0's test-video source is the only validated path. Phase 1a Day 6 staff cohort is on real screen-capture; install / capture issues surface there. Pause Phase 1a if needed. |
| **Two-stage flag pattern doesn't clean up between cohorts.** | Phase 1 (any cutover) | Pre-Phase-1a unit test (per ADR 0012) verifies hash-stable cohort assignment + kill-switch precedence. |
| **Adapter v0.3 coverage classifier under-trains.** | Phase 1.1 | Phase 1c indefinitely delayed. Start v0.3 training-data collection during Phase 1a observation window; pipeline the data work. |

## Calendar markers — what to communicate when

Markers from the previous revision are still right, but they slide by Phase 0 remainder's calendar (8–10 working days from today before Phase 1a Day -3 fires).

| When | Audience | Message |
|---|---|---|
| **Phase 0 remainder kickoff** | Eng team | "Phase 0 isn't done. M4.5 + M5c + OCR reform start Monday. PR #62 / #63 stay open." |
| **Phase 0 remainder close** | Eng team | "Phase 0 acceptance criteria all pass on real footage. PR #62 + #63 merge today." |
| **Phase 1a Day 1** | Eng team | "Drill Lab cutover starts. 5-day build, 7-day observation, decision Day 13." |
| **Phase 1a Day 6** | Staff cohort | "Drill Lab is on the real pipeline for staff. Run a drill, flag anything weird." |
| **Phase 1a Day 9** | Trusted-player cohort | "You're on the Phase 1a beta. Feedback channel is …" |
| **Phase 1a Day 13** | All Competitive+ users (if pass) | "Drill Lab now uses live screen-vision. Expect formation feedback within 2 seconds." |
| **Phase 1b Day 13** | All Competitive+ users (if pass) | "SimLab + Gameplan now live with the same pipeline." |
| **Phase 1.1 Day 10** | Internal only (under-the-hood) | (No external message; v0.2/v0.3 are internal upgrades that gate Phase 1c.) |
| **Phase 1c Day 13** | All Competitive+ users (if pass) | "Arsenal weapons trigger live. War Room shows live coverage banners." |

## What this timeline does NOT cover

- **Phase 0 remainder details** — see [0-vaf-remaining-milestones.md](../phase-completions/0-vaf-remaining-milestones.md).
- **Phase 2 (Analytics Film Room).** Calendar-anchored separately; depends on Phase 1c stability + frame cache (per ADR 0002).
- **Phase 3 (mock deletion).** Calendar-anchored 30 days after Phase 1c per ADR 0004.
- **Other titles' adapters** (NBA 2K26, FPS adapters). Each gets its own multi-week milestone after Madden adapters stabilise.
- **VoiceForge integration.** Lives on a parallel track; Phase 1 is vision-only.

## Reference: ADR 0006 budget is preserved

The 80 ms per-frame budget for adapter v0.1 (per ADR 0006) is **not** revised by this work. The original budget assumed expected OCR + classifier costs of ~25 ms per frame. Real EasyOCR-on-CPU at ~30 ms × 8 regions broke that expectation by violating the cadence assumption (OCR was supposed to run on snap events, not every frame). The fix is structural: snap-event-triggered OCR brings the cost back under budget. If Milestone 3 lands and p95 is still over 80 ms, **then** a superseding ADR is the right move with measured rationale. Not before.

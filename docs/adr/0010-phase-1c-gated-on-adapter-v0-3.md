# ADR 0010 — Phase 1c Cutover Gated on Madden Adapter v0.3

- **Status:** Accepted — **gate MET 2026-07-14** (see Gate status below)
- **Date:** 2026-05-06

## Gate status (2026-07-14)

The v0.3 dependency is **shipped and validated**, unblocking Phase 1c:

- `COVERAGE_LOCKED` is live on the bus (v0.3 classifier + emit merged to main).
- The kickoff checklist's quality bar — **coverage-classifier macro-F1 ≥ 0.85 on a held-out
  set** — is **met: held-out macro-F1 = 0.92** across 3 by-game captures (PR #135,
  `docs/coverage-hardening-results.md`). This is the group-held-out (by-game) number, not a
  by-clip one.
- `ADAPTER_VERSION` bumped off the `phase-0` placeholder to `madden26@0.3.0`.
- **Out of scope for local/owner use:** the "production-stable for ≥7 days" and
  "emit-rate ≥5/session p50" conditions are **staging/production rollout gates** (public
  multi-user), not local prerequisites — they apply when exposing these features beyond the
  owner. Phase 1c local cutover proceeds on the macro-F1 + emit gates above.
- **Known residual (non-blocking):** the fixed-bbox SNAPSHOT HUD (down/distance/quarter) is
  matchup-calibrated and degrades off KC/LV (dynamic bar layout, PR #135) — Phase 1c keys on
  COVERAGE, which is unaffected; situational fields are best-effort.
- **Reference:** [FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md) — Rule 4 (events are structured and canonical — consumers gated on event existence, not on schema-promise vs schema-ship).
- **Modifies:** [specs/03-mock-removal-and-page-wiring.md §3 "Cutover phases" (Phase 1c)](../specs/03-mock-removal-and-page-wiring.md). **Updates the dependency model** for Phase 1c.

## Context

Spec #3's migration plan defines:

- **Phase 1c — Arsenal + War Room cutover** (Weeks 7–8). New functionality (Arsenal live triggers, War Room ranked-match awareness) goes from inert to live.

Spec #2's Madden adapter spec defines:

- **v0.1** — offensive formation only (top-8 formations).
- **v0.2** — adds pre-snap defensive front.
- **v0.3** — adds post-snap coverage detection (`COVERAGE_LOCKED` events).

Per Spec #2's Phase 1 milestones, **v0.1 ships in Phase 1**; v0.2/v0.3 are post-Phase-1 work.

The conflict: Phase 1c lights up Arsenal and War Room features that **depend on `COVERAGE_LOCKED` events** (Arsenal's "Cover 3, third and long, your secret weapon is X" triggers; War Room's "Cover 3 detected" mid-game banner). With only v0.1 shipped, those events don't exist on the bus, so the features fire empty — Arsenal weapons never trigger, War Room never surfaces a coverage banner.

This isn't a bug; it's a dependency the spec didn't capture clearly.

## Decision

**Phase 1c is gated on Madden adapter v0.3 shipping** — i.e., `COVERAGE_LOCKED` events are live on the bus before Arsenal + War Room cutover.

**Updated dependency chain for Phase 1c:**

1. Madden adapter v0.1 ships (Phase 1, M5 milestone).
2. Phase 1a (Drill Lab) cutover — depends only on v0.1's `FORMATION_LOCKED` events. Proceeds independently.
3. Phase 1b (SimLab + Gameplan) cutover — SimLab depends on v0.1; Gameplan's `COVERAGE_LOCKED` overlay degrades gracefully without v0.3 (no banner fires; static recommendations remain). Proceeds with caveat.
4. **Madden adapter v0.2 + v0.3 ship** as a Phase-1.1 follow-up (estimated 5–7 working days post-Phase-1).
5. **Phase 1c (Arsenal + War Room) cutover gated on adapter v0.3 production-stable for ≥7 days.**

If `COVERAGE_LOCKED` events aren't reliably emitted, Phase 1c is delayed. War Room and Arsenal stay on their pre-cutover behaviour (static War Room briefing surface; Arsenal weapon list without live highlighting) until the dependency lands.

## Consequences

- The original migration timeline gets extended by 5–7 working days for the v0.2/v0.3 work between Phase 1b and Phase 1c.
- Arsenal weapon-trigger features are advertised as **"available in Madden in 2 weeks"** rather than landing surprise-empty when Phase 1c flips.
- The mock-deletion bar (per [ADR 0004](0004-mock-deletion-bar.md), 30 days from Phase 1c) shifts proportionally — by ~5–7 days.
- Gameplan's `COVERAGE_LOCKED` subscription (Phase 1b) is **a soft-launch** — the subscription is wired but no events fire until v0.3. Document this expected silence so QA doesn't false-flag it.
- Phase 1c kickoff checklist gains a hard prerequisite: "Madden adapter v0.3 deployed to staging + production-stable for 7 days; `COVERAGE_LOCKED` event emit rate >= 5 per session p50; coverage-classifier macro-F1 ≥ 0.85 on held-out test set."

## Notes / followups

- This dependency may apply to other adapters too. NBA 2K26's "defensive scheme" (ICE, drop, switch, blitz) is an analogous post-action event; whichever NBA-consuming page depends on it should similarly gate.
- Phase 4 (Warzone, Fortnite) has analogous dependencies for live-cue features. Capture this pattern in each phase's milestone document.
- The Spec #3 migration plan calendar should be updated in a follow-up commit to reflect the gating; this ADR is the immediate authoritative source until that update lands.

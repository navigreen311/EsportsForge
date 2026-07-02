# ADR 0012 — Two-Stage Feature-Flag Pattern for Phase 1 Cutovers

- **Status:** Accepted
- **Date:** 2026-05-07
- **Reference:** [FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md) — Rule 1 (multi-dimensional from day one — features must remain togglable per-cohort, not all-or-nothing) and Rule 4 (consumers gate on event existence; the flag layer enforces "is this user in the rollout?" without leaking that decision into adapter logic).
- **Modifies:** [specs/03-mock-removal-and-page-wiring.md §3 "Cutover phases"](../specs/03-mock-removal-and-page-wiring.md). Adds a flag-shape contract for every Phase 1 cutover.

## Context

Phase 0's lessons learned (L4 in the Phase 0 completion doc) flagged that a single feature flag per cutover (e.g., `drill_lab_uses_real_vision`) is not enough. Each cutover needs **two independent levers**:

1. **A master kill-switch** — flips the entire cohort out of real-vision back to mocks instantly. Used in incidents.
2. **A widening flag** — controls who is in the cohort. Cohort starts at 5% canary, widens via dial-up.

A single Boolean flag can't represent both. If the same flag controls both "is anyone using real vision" and "what fraction of users", an incident response (kill-switch) fights with planned rollout (widening). The team encountered this exact issue during the SiteForge / Atlas rollout (per the Greenstone PCA postmortem); we are not relitigating it.

The Phase 1a kickoff brief already specifies a two-flag shape (`vaf_kill_switch` + `vaf_drill_lab_cohort_pct`), but it lives only in the brief. This ADR formalises the pattern across **every Phase 1 cutover** so 1a, 1b, 1c, and 1.1 ship the same shape.

## Decision

Every Phase 1 cutover (Drill Lab, SimLab, Gameplan, Arsenal, War Room, and the Madden v0.2/v0.3 follow-up) ships **two flags**:

| Flag | Purpose | Default | Owner |
| --- | --- | --- | --- |
| `vaf_master_kill_switch` | Force every consumer back to mocks. **Single boolean, applies to all titles + features.** | `false` | Operator on-call |
| `vaf_<feature>_cohort_pct` | Percentage of eligible users routed to real-vision for this feature. Integer 0–100. | `0` | Cutover lead |

**Behaviour rules:**

1. **Kill switch wins.** When `vaf_master_kill_switch=true`, every consumer reads from mocks regardless of cohort_pct. No exception, no per-feature override.
2. **Cohort assignment is sticky for the user.** `hash(user_id, feature_name) mod 100 < cohort_pct` — same user, same answer for the lifetime of the rollout. Prevents flicker mid-session.
3. **Cohort_pct widens monotonically.** Each cutover's runbook defines the dial-up schedule (5% → 25% → 50% → 100% per the Phase 1a brief). Lowering it after dial-up is allowed for incident response, but doing so does **not** retroactively force out users already in the cohort — only the kill-switch does that.
4. **Flag reads are cached for ≤60 seconds per user.** Avoids hammering the Settings table on every page load. Trade-off accepted: an emergency kill-switch flip propagates within 60 seconds (vs. instant); operators are briefed.
5. **Each cutover gets its own `cohort_pct`.** No sharing between Drill Lab, SimLab, etc. Independent dial-up per feature.

## Consequences

- Every cutover PR is responsible for adding **two** Settings rows (`vaf_master_kill_switch` once, `vaf_<feature>_cohort_pct` per feature). PR template gets a checkbox for this.
- The settings_admin frontend ([P5 of the tournament-settings audit work](../../frontend/src/app/settings/admin)) gains a "VAF cutovers" panel with one row per cohort flag plus the master kill-switch.
- A unit test in `backend/tests/test_feature_flags.py` asserts: (a) kill-switch overrides cohort, (b) hash-based cohort assignment is stable, (c) cohort widening doesn't flicker users out.
- Flag-cache TTL becomes a **runbook-documented** number (60 s). On-call playbook explains "when you flip the kill-switch, expect ≤60 s before all consumers honour it; if you need faster, restart the affected workers."
- **The kill-switch is shared across titles** — a Madden adapter incident affects all titles' real-vision routing, not just Madden's. Justified: in Phase 1, only Madden is wired to real-vision anyway. When NBA / FPS adapters land, this ADR's "single kill-switch" rule may need a per-title revision; flag the open-question now.

## Followups

- Phase 1a kickoff brief is already aligned. Verify Phase 1b / 1c / 1.1 briefs (when written) include the two-flag shape.
- Capture a follow-up question in the Phase 2 kickoff: "Do we need per-title kill-switches, or is the global one still right?"
- Add a `make flags-status` target that prints the current cohort_pct for every VAF feature alongside the master kill-switch state. Helpful during a cutover.

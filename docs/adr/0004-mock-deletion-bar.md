# ADR 0004 — Mock Deletion Bar

- **Status:** Accepted
- **Date:** 2026-05-06
- **Reference:** [FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md) — Rules 2 + 3 (mock removal is the moment the codebase stops violating these rules).
- **Modifies:** [specs/03-mock-removal-and-page-wiring.md §5 Q4](../specs/03-mock-removal-and-page-wiring.md).

## Context

After Phase 1 cutover completes (all six pages on the real pipeline), the simulated `vision_client.py` and its sibling stub modules become dead code. A deletion bar — the duration of stable production usage required before the mock is permanently removed — was an open question.

Four options were considered:

- **(a)** 30 days of all-page stability.
- **(b)** 60 days.
- **(c)** 90 days.
- **(d)** Tied to error-rate metric (e.g., delete when <0.1% errors for 14 consecutive days).

## Decision

**Adopt (a) — 30 days of all-page stability before mock deletion.**

**Explicitly reject (d).** Metric-tied deletion is gameable: error rates are noisy, the team will spend cycles arguing whether 0.11% counts. A fixed date is unambiguous and forces decision discipline.

## Consequences

- Phase 3 of the migration plan (mock deletion) is calendar-anchored to Phase 1c completion + 30 days.
- Rollback path remains available throughout the 30-day window — operators can flip any feature flag back to the mock within 30 seconds.
- The mock code lives in tree only until Phase 3, then is deleted in one PR (delete `vision_client.py`, the four sibling stub modules, and the deprecated endpoints).
- After deletion, rollback is a git revert, not a feature flag flip — slower but possible.

## Notes / followups

- The 30-day window includes at least one weekend, two Monday-morning surges, and one game-patch cycle. If a critical bug surfaces later than that, it's a forward-fix in the real pipeline, not a rollback to mock.
- If the team has nervous energy at day 28, that's a signal — investigate the source before extending the window. Don't extend reflexively.

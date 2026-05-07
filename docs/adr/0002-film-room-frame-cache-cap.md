# ADR 0002 — Film Room Frame Cache Cap

- **Status:** Accepted
- **Date:** 2026-05-06
- **Reference:** [FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md) — Rule 3 (logic in the Forge: retention policy is a core-service concern, not a page concern).
- **Modifies:** [specs/03-mock-removal-and-page-wiring.md §5 Q2](../specs/03-mock-removal-and-page-wiring.md), [specs/02-visionaudioforge-core.md §5 "Frame retention"](../specs/02-visionaudioforge-core.md).

## Context

The Analytics Film Room is the only consumer that opts into frame retention. Without a cap, S3 storage + bandwidth costs scale with concurrent recording players and session length — at 1 fps × 50 KB JPEG × hours of session × N players, costs can spike unpredictably.

Four options were considered:

- **(a)** 30-min cap, opt-in, default off — ~$125/mo at projected mix.
- **(b)** 60-min cap, opt-in, default off — ~$250/mo.
- **(c)** Tier-gated (30 min Competitive, unlimited Elite) — ~$200–500/mo.
- **(d)** No cap, only 7-day TTL — risk of $500–2000/mo bandwidth surges.

## Decision

**Adopt (a) — 30-min recording cap per session, opt-in, default off.**

**Document the 30-minute cap in the Analytics Film Room UI** so players understand the constraint upfront before they assume "record this session" means the full game.

## Consequences

- VAF core service enforces a 30-minute hard cap on the per-session frame cache. Recording stops automatically at 30 min; remainder of the session is event-only (no frames cached).
- Frame cache lifecycle: 7-day TTL via S3 lifecycle policy.
- Frontend UI shows the cap explicitly: "Recording — 30 minutes max per session" near the toggle.
- Cost ceiling stays predictable; budget alarms set at $200/mo (60% over projection).
- Reconsider (c) tier-gated when Elite tier conversion data is available.

## Notes / followups

- Player-experience review of the UI copy: the constraint should feel like a feature ("cleaner highlights") not a limit ("we cut you off"). Coordinate with content/UX before Phase 2 ships.
- Track usage: how often do players hit the 30-min cap? If >20%, that's signal to consider (b) or (c).

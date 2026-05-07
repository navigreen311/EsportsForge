# ADR 0001 — Feature Flag Infrastructure

- **Status:** Accepted
- **Date:** 2026-05-06
- **Reference:** [FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md) — Rule 5 (adapters added without core changes; the migration path itself is a Forge concern, not a per-consumer concern).
- **Modifies:** [specs/03-mock-removal-and-page-wiring.md §5 Q1](../specs/03-mock-removal-and-page-wiring.md).

## Context

The migration plan in Spec #3 needs per-page feature flags (`VAF_REAL_PIPELINE_ENABLED_DRILL_LAB` and similar) to gate gradual cutover from the mocked vision pipeline to the real one. The EsportsForge backend has no dedicated feature-flag service today.

Three options were considered:

- **(a)** LaunchDarkly integration — industry-standard, per-user / per-tier targeting, ~$200/mo + 1–2 days dev.
- **(b)** Env-var-driven flag table in Settings — zero new infra, ~half-day dev, no per-user targeting.
- **(c)** Reuse the Integrity Mode mechanic as a proxy (Offline Lab → real pipeline; Ranked → mock).

## Decision

**Adopt (b) — env-var-driven flag table in Settings.** Skip LaunchDarkly until usage justifies it.

**Explicitly reject (c).** Conflating Integrity Mode (a player-facing competitive-fairness signal) with engineering rollout knobs is semantically wrong and would prevent players from understanding their own competitive context.

## Consequences

- A new `VAF_REAL_PIPELINE_ENABLED_<PAGE>` table is added to `settings.json` (or equivalent), readable by both backend and frontend.
- Flag flips are an engineer-driven `settings.json` edit + restart of one ECS task. No UI for non-engineers to flip.
- No per-user / per-tier targeting in v1. All-or-nothing per flag.
- Audit history of flag flips comes from git blame on `settings.json`.
- Re-evaluate moving to LaunchDarkly when the platform has 30+ flags or when per-user targeting becomes operationally necessary.

## Notes / followups

- Document the flag list and how to flip them in an ops runbook before Phase 1a.
- When LaunchDarkly is eventually adopted, this ADR is superseded by a new ADR; the env-var path remains as a fallback/dev affordance only.

# ADR 0003 — Webhook Delivery Durability (v1)

- **Status:** Accepted
- **Date:** 2026-05-06
- **Reference:** [FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md) — Rule 4 (events are structured and canonical; durability is part of "canonical").
- **Modifies:** [specs/03-mock-removal-and-page-wiring.md §5 Q3](../specs/03-mock-removal-and-page-wiring.md), [specs/02-visionaudioforge-core.md §8 "Webhook delivery failure"](../specs/02-visionaudioforge-core.md).

## Context

The VAF core service POSTs events to the EsportsForge backend via webhook. v1 is fire-and-forget with 5 retries (250 ms → 500 ms → 1 s → 2 s → 4 s exponential backoff). If the EsportsForge backend is down during a critical event (`MATCH_STARTED`), the War Room subscriber misses a state transition.

Three options were considered:

- **(a)** In-process v1 (current plan) — estimated 0.1–0.5% loss per session, $0 cost.
- **(b)** Redis Streams durable bus — <0.01% loss, ~$30/mo + ~3 days dev.
- **(c)** S3 dead-letter on webhook failure — manual replay only, ~$5/mo.

## Decision

**Adopt (a) — in-process v1 with fire-and-forget + 5 retries.**

**Add explicit instrumentation requirements:**
- Log webhook delivery failure rate per `session_id`.
- Alarm threshold: **>0.1% sustained over 60 minutes**.

**Auto-upgrade trigger:** If the alarm fires during Phase 1a or Phase 1b, **upgrade to Redis Streams durable bus before Phase 1c (War Room cutover)**. War Room's `MATCH_STARTED` is the most loss-sensitive event in the platform, and the cost of a missed state transition there is high.

## Consequences

- Phase 0 of the build includes webhook-delivery instrumentation as a first-class deliverable, not an afterthought.
- Operations dashboard tracks per-session webhook delivery success rate. Alert hooks into oncall paging.
- If alarm fires, Phase 1c is delayed until Redis Streams ships. Phase 1a (Drill Lab) and 1b (SimLab + Gameplan) may proceed even with the alarm because their events (`FORMATION_LOCKED`, `PLAY_STARTED`, `COVERAGE_LOCKED`) are higher-frequency and partial loss is recoverable from the next event.
- Redis Streams migration plan stays documented in [specs/02 §"Open architectural questions"](../specs/02-visionaudioforge-core.md) for ready execution if the trigger fires.

## Notes / followups

- Build the dashboard panel + alarm rule before Phase 1a goes live, not after.
- Document the upgrade-decision criteria in the Phase 1c kickoff checklist so the team doesn't accidentally proceed with the alarm in flight.

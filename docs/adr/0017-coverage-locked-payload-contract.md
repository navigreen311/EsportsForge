# ADR 0017 — COVERAGE_LOCKED Payload Contract + Coverage Vocabulary

- **Status:** Accepted
- **Date:** 2026-07-03
- **Reference:** [CLAUDE.md](../../CLAUDE.md). Pins a contract *ahead of* the producer, per the Forge "events are structured and canonical" principle (consumers gate on event existence, not schema-promise — ADR 0010 reference to FORGE_ARCHITECTURE_PATTERN.md Rule 4).
- **Establishing case:** Phase 1b Gameplan soft-launch (`b3240a4`) subscribes to `COVERAGE_LOCKED` with a documented-silent seam (`frontend/src/lib/gameplan/coverageHighlight.ts`); this ADR pins the payload that seam will consume at v0.3.
- **Modifies:** [schemas/events.py](../../services/visionaudioforge/app/schemas/events.py) `FootballPayload` — adds `defensive_coverage`.
- **Related:** [ADR 0010](0010-phase-1c-gated-on-adapter-v0-3.md) (v0.3 gates Phase 1c; coverage classifier deliverable), [ADR 0014](0014-ocr-overlay-over-cnn-for-formation-signals.md) (the free-str + documented-canonical-set pattern this mirrors), [spec 03 §117](../specs/03-mock-removal-and-page-wiring.md) (Gameplan kill-sheet auto-highlight — the v0.3 consumer).

## Context

`COVERAGE_LOCKED` is a defined `EventType` (`enums.py`) but is **emitted by nothing** — the Madden adapter's `detect_coverage` is a v0.3 stub returning `None`, and no model exists (recon: no weights, no coverage training data, footage-adequacy unproven — M5c found broadcast footage did not expose enough detail for fine formations, which forced the formation OCR pivot; coverage is post-snap with **no** overlay to OCR, so it has no such escape hatch). v0.3 (the classifier) is therefore **blocked** as a code session.

The Phase 1b Gameplan cutover shipped the subscription as a documented soft-launch (ADR 0010 §45). Its highlight seam (`deriveCoverageHighlight`) can't be built until it knows *what field* carries the coverage and *what values* it holds. Today there is no such field: `FootballPayload` is `extra="forbid"`, so a coverage value cannot ride in an ad-hoc key, and the only defensive field (`defensive_formation`) is actually the **v0.2 pre-snap front**, a different signal — and was mislabeled in-code as "None until v0.3."

This ADR pins the **contract** now (schema field + coverage vocabulary), decoupled from the (blocked) model, so the frontend seam has a stable target. **This is a contract for a producer that does not exist and whose feasibility is unproven; the vocabulary is a domain-grounded guess, revisable when the model ships.**

## Decision

1. **Add `defensive_coverage: str | None = None` to `FootballPayload`** — the sanctioned carrier for the v0.3 post-snap coverage shell on a `COVERAGE_LOCKED` event. Kept **distinct** from `defensive_formation` (v0.2 pre-snap front); the two are separate signals (`detect_defensive_front` vs `detect_coverage`). The mislabeled `defensive_formation` comment is corrected to "v0.2 front."

2. **Type is free `str`, NOT a pydantic enum** — mirroring `offensive_formation` (free-str with the canonical-8 documented, not enforced; ADR 0014). A hard `CoverageEnum` would **reject an unforeseen real model label at v0.3 and crash validation** on the ingest path. The vocabulary is documented and revisable, not enforced by the schema.

3. **Documented coverage vocabulary (football-standard shells)** — the value SHOULD be one of:

   | Value | Notes |
   |---|---|
   | `Cover 0` | pure man, no deep help (man-principle) |
   | `Cover 1` | man-free (single high safety) |
   | `Cover 2` | 2-deep zone |
   | `Cover 3` | 3-deep zone |
   | `Cover 4 (Quarters)` | 4-deep quarters |
   | `Cover 6` | quarter-quarter-half |

   Documented variants (emit if the model distinguishes them): `Cover 2-Man`, `Cover 1-Robber`. **Man vs zone is derivable** (0/1 = man-principle; 2/3/4/6 = zone) — no separate field. `Cover 5` is nonstandard (colloquially 2-Man) and is **excluded**.

   Deferred to model-time (not added speculatively now): a `defensive_coverage_family` canonical tag (mirroring `offensive_formation_family`), if the model's raw labels need canonicalization.

4. **`beats` (frontend) — documented v0.3 plan, no code change now.** Spec §117 assumes `Play.beats[]` (array, `contains`); the real field is `beats?: string` (free-text) with 8+ consumers across 5 files, including `COVERAGE_MATRIX[play.beats]` (a lookup **keyed on the string**). At v0.3, when `deriveCoverageHighlight` is built: migrate `Play.beats → string[]` to match §117's `contains` semantics, and rework the consumers (re-key `COVERAGE_MATRIX`, normalize values). **Normalization is required regardless of string-vs-array**, because today's `beats` already holds compound and non-coverage values (`"Cover 3 / Cover 4"`, `"Nickel/Dime Packages"`, `"Aggressive LB Play"`, `"Man Blitz"`) — a coverage-name normalization layer must map the pinned vocabulary to whatever `beats` records. Migrating now would break `COVERAGE_MATRIX` across 5 files to serve unbuilt logic against a non-emitting signal, so it is deferred.

## Alternatives considered

1. **Overload `defensive_formation` for coverage.** Rejected: front (v0.2) and coverage (v0.3) are distinct signals from distinct detectors; one field would conflate them and lose the pre-snap/post-snap distinction.
2. **Hard `CoverageEnum`.** Rejected: rigidity crashes ingest validation on any label the (unbuilt) model emits outside the guessed set. Free-str + documented set is the pattern that carried `offensive_formation` through v0.1.
3. **Add `defensive_coverage_family` now.** Rejected: speculative structure for a signal with no producer; add at model-time if canonicalization is needed.
4. **Migrate `Play.beats → string[]` now.** Rejected: multi-file change (breaks `COVERAGE_MATRIX[play.beats]`) serving unbuilt highlight logic + a non-emitting signal. Documented for model-time.
5. **Wait and pin at model-time.** Rejected for the field + vocabulary (the cheap, domain-stable part): pinning now gives the Gameplan seam a stable target and surfaces the front-vs-coverage mislabel. The model itself stays deferred.

## Consequences

- `COVERAGE_LOCKED` has a schema carrier (`defensive_coverage`) and a documented vocabulary; the Gameplan seam has a stable target to build against at v0.3.
- The `defensive_formation` mislabel (v0.2 front, not v0.3) is corrected.
- **Nothing emits coverage.** The field is inert (`None`) until the v0.3 classifier ships. There is **no live/model verification** — the schema test (field accepts str/None; `extra="forbid"` still rejects undeclared keys) is the only proof. The vocabulary is a **considered domain guess**, not a validated label set, and is explicitly revisable when the model exists.
- The contract is `extra="forbid"`-safe: adding the declared field is the *only* way a coverage value can ride, so the pin is load-bearing (an ad-hoc key would be rejected).

## Followups

- **v0.3 classifier** (ADR 0010) — the blocked producer: labeled post-snap coverage footage, a trained model at macro-F1 ≥ 0.85, footage-adequacy validation, then wire `detect_coverage → state_assembler` to emit `COVERAGE_LOCKED` populating `defensive_coverage`.
- **Frontend `beats` migration** (this ADR §4) — execute at model-time alongside `deriveCoverageHighlight`.
- **Missing contract doc (tracked finding).** `services/visionaudioforge/app/schemas/events.py` cites *"Locked surface per docs/integrations/visionaudioforge/03-event-bus-contract.md"* — that file **does not exist**. This ADR is the home for the coverage-contract decision; the broader dangling reference (the whole event-bus contract's cited source-of-truth is absent) is noted here for later reconciliation, not fixed in this change.

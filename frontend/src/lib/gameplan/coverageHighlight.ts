/**
 * Gameplan coverage-highlight seam — Phase 1b (Gameplan cutover).
 *
 * SOFT-LAUNCH (ADR 0010 §45): Gameplan subscribes to COVERAGE_LOCKED, but the
 * Madden adapter emits NO coverage events until v0.3. So in v0.1 `lastEvent` is
 * always null here and this always returns null (graceful empty) — the
 * kill-sheet renders unchanged. The subscription is genuinely wired and will
 * light up automatically when v0.3 ships; this function is the single seam
 * where the kill-sheet auto-highlight lands.
 *
 * v0.3: derive the detected coverage from the COVERAGE_LOCKED payload and return
 * the kill-sheet plays that beat it — spec #03 §117 (highlight plays whose
 * `beats` match the coverage + a "Cover 3 detected — try …" banner + 30s
 * timeout). Deferred now because FULL is unbuildable in v0.1:
 *   - the coverage payload contract is unpinned (`defensive_formation` is
 *     null-until-v0.3; there is no finalized coverage-value field),
 *   - the coverage-name vocabulary the classifier emits does not exist yet
 *     (a v0.3 macro-F1 deliverable), and
 *   - `Play.beats` is free-text (`string`, not the `beats[]` array spec §117
 *     assumes) with no coverage vocabulary — see the v0.3 beats-vocabulary note.
 * Matching two undefined vocabularies against an invented fixture would prove
 * nothing real and guarantee rework, so v0.1 stays silent by design.
 */
import type { EventEnvelope } from '@/hooks/useVisionEvents';

export interface CoverageHighlight {
  /** The detected coverage (e.g. "Cover 3"), from the COVERAGE_LOCKED payload. */
  coverage: string;
  /** ids of kill-sheet plays that beat the detected coverage. */
  playIds: string[];
}

export function deriveCoverageHighlight(
  lastEvent: EventEnvelope | null,
): CoverageHighlight | null {
  // v0.1: no COVERAGE_LOCKED ever fires (soft-launch silence, ADR 0010 §45) —
  // inert whether lastEvent is null or (defensively) a surfaced coverage event.
  if (!lastEvent) return null;
  // v0.3: replace with real coverage -> beats matching once the payload
  // contract + coverage vocabulary exist. Until then stay silent rather than
  // match invented data.
  return null;
}

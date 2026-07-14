/**
 * Gameplan coverage-highlight seam (v0.3 — OCR-of-play-call coverage leg).
 *
 * When the Madden adapter emits a COVERAGE_LOCKED (the committed defensive
 * coverage, read off the pre-snap coach-cam play-art), derive the kill-sheet
 * plays that beat it — spec #03 §117 (highlight plays whose `beats` match the
 * detected coverage + a "Cover 3 detected — try …" banner + 30s timeout; the
 * banner/timeout live in the Gameplan page, this module is the pure matcher).
 *
 * v0.1 was inert-by-design: the adapter emitted no coverage and the two
 * vocabularies (the coverage-value field, the classifier's coverage names)
 * didn't exist, so matching would have been against invented data. Both now
 * exist on `main`: the payload carries `defensive_coverage` (canonical, e.g.
 * "Cover 3" / "Cover 2-Man") and the classifier emits Cover 0/1/2/2-Man/3/4/6/9.
 * `Play.beats` remains free-text ("Cover 3", "Cover 2 Zone", "Man Coverage",
 * "Cover 3 / Cover 4"), so the match is a normalized "Cover N" shell match plus
 * a man/zone rule (see playBeatsCoverage). Coverages with no counter-play in the
 * sheet (e.g. Cover 6/9) return null — no highlight rather than an empty one.
 */
import type { EventEnvelope } from '@/hooks/useVisionEvents';

export interface CoverageHighlight {
  /** The detected coverage (e.g. "Cover 3"), from the COVERAGE_LOCKED payload. */
  coverage: string;
  /** ids of kill-sheet plays that beat the detected coverage. */
  playIds: string[];
}

/** A play's minimal shape for matching — just its id and free-text `beats`. */
export interface HighlightablePlay {
  id: string;
  beats?: string | null;
}

/**
 * Does a play's free-text `beats` counter the detected coverage?
 *
 *  - Shell match: the "Cover N" number in the coverage matches a "cover N" token
 *    in `beats` (word-bounded, so "cover 2" ≠ "cover 20"). "Cover 2-Man" keeps
 *    shell 2, so it also lights Cover-2 beaters. Handles "Cover 3 / Cover 4".
 *  - Man rule: a man coverage — any "-Man", or Cover 0/1 (man-based) — also lights
 *    plays that beat a generic "Man" look ("Man Coverage", "Man Blitz").
 */
export function playBeatsCoverage(beats: string, coverage: string): boolean {
  const b = beats.toLowerCase();
  const cov = coverage.toLowerCase();
  const num = cov.match(/cover\s*(\d+)/)?.[1];
  const shellMatch = num != null && new RegExp(`cover\\s*${num}\\b`).test(b);
  const isMan = /\bman\b/.test(cov) || /cover\s*[01]\b/.test(cov);
  const manMatch = isMan && /\bman\b/.test(b);
  return shellMatch || manMatch;
}

export function deriveCoverageHighlight(
  lastEvent: EventEnvelope | null,
  plays: readonly HighlightablePlay[],
): CoverageHighlight | null {
  if (!lastEvent) return null;
  const coverage = lastEvent.payload.defensive_coverage;
  if (typeof coverage !== 'string' || coverage.length === 0) return null;
  const playIds = plays
    .filter((p): p is HighlightablePlay & { beats: string } =>
      typeof p.beats === 'string' && playBeatsCoverage(p.beats, coverage),
    )
    .map((p) => p.id);
  if (playIds.length === 0) return null; // detected, but nothing in the sheet beats it
  return { coverage, playIds };
}

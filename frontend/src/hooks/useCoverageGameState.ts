/**
 * useCoverageGameState — Phase 1c coverage→game-state bridge.
 *
 * The shared bridge both Arsenal (1c.3) and War Room (1c.2) consume: it turns the
 * live COVERAGE_LOCKED stream into a small game-state object (the detected coverage +
 * the payload's down/distance), deduped by `event_id` so a re-surfaced event (React
 * re-render, or a reconnect that replays the latest event as a fresh object) doesn't
 * re-fire. Analog of `useSimLabAutoRep` (event → action, deduped) but returning STATE
 * rather than counting reps.
 *
 * Consumers: War Room reads `coverage` for its live banner; Arsenal fires its
 * `/arsenal/trigger` in `onCoverage` (once per new coverage) and threads the coverage
 * into `game_state`. Pure — provisioning + subscription stay in the page (useVisionEvents);
 * this hook is subscription-agnostic and takes the already-filtered `lastEvent`.
 *
 * Situational fields (down/distance) are best-effort: the fixed-bbox SNAPSHOT HUD is
 * matchup-calibrated and degrades off KC/LV (PR #135). Coverage — the load-bearing signal —
 * is unaffected (it reads on-field play-art, not the bar).
 */
import { useEffect, useRef, useState } from 'react';

import type { EventEnvelope } from './useVisionEvents';

export interface CoverageGameState {
  /** Detected defensive coverage (e.g. "Cover 3"), or null before any read. */
  coverage: string | null;
  /** Best-effort down/distance from the COVERAGE_LOCKED payload (may be null). */
  down: number | null;
  distance: number | null;
  /** event_id of the coverage read — the dedupe key consumers can rely on. */
  eventId: string | null;
}

export const EMPTY_COVERAGE_STATE: CoverageGameState = {
  coverage: null,
  down: null,
  distance: null,
  eventId: null,
};

export interface UseCoverageGameStateOptions {
  /** Latest COVERAGE_LOCKED from useVisionEvents (already filtered to that type). */
  lastEvent: EventEnvelope | null;
  /** Called exactly once per NEW COVERAGE_LOCKED event_id (e.g. fire a weapon trigger). */
  onCoverage?: (state: CoverageGameState) => void;
}

function num(v: unknown): number | null {
  return typeof v === 'number' ? v : null;
}

export function useCoverageGameState({
  lastEvent,
  onCoverage,
}: UseCoverageGameStateOptions): CoverageGameState {
  const [state, setState] = useState<CoverageGameState>(EMPTY_COVERAGE_STATE);
  // event_id of the last coverage that updated state — the dedupe key.
  const lastEventId = useRef<string | null>(null);
  // Keep the latest onCoverage without making it an effect dependency (so a new
  // callback identity each render doesn't re-fire the trigger).
  const onCoverageRef = useRef(onCoverage);
  onCoverageRef.current = onCoverage;

  useEffect(() => {
    if (!lastEvent || lastEvent.event_type !== 'COVERAGE_LOCKED') return;
    if (lastEvent.event_id === lastEventId.current) return; // re-surfaced event — ignore
    const cov = lastEvent.payload.defensive_coverage;
    if (typeof cov !== 'string' || cov.length === 0) return; // no coverage in payload
    lastEventId.current = lastEvent.event_id;
    const next: CoverageGameState = {
      coverage: cov,
      down: num(lastEvent.payload.down),
      distance: num(lastEvent.payload.distance),
      eventId: lastEvent.event_id,
    };
    setState(next);
    onCoverageRef.current?.(next);
  }, [lastEvent]);

  return state;
}

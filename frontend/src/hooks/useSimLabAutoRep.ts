/**
 * useSimLabAutoRep — Phase 1b (SimLab cutover).
 *
 * SimLab analog of `useDrillLabAutoRep`. Maps vision events to SimLab reps:
 * one `FORMATION_LOCKED` (which fires once per play-call screen, ADR 0015 /
 * §4c) → exactly one rep. Deduped by `event_id` so a re-surfaced event (React
 * re-render, or a reconnect that replays the latest event as a fresh object)
 * never double-counts.
 *
 * SimLab keys on FORMATION_LOCKED — the only pre-snap signal the Madden adapter
 * emits in v0.1 (spec #03 §94's PLAY_STARTED/PLAY_ENDED are not emitted until
 * v0.2/v0.3, a documented soft-launch deferral; timeline §37 + ADR 0010 §34
 * key SimLab on FORMATION_LOCKED for v0.1).
 *
 * Rep-counting boundary kept OUT of `useVisionEvents` (which stays
 * counting-agnostic). The actual rep record lives in the page (`handleRepDetected`
 * / `setReps`); this unit just fires `onRep` once per new formation event.
 * Event-display-only — no success grading (that is coaching, deferred).
 */
import { useEffect, useRef } from 'react';

import type { EventEnvelope } from './useVisionEvents';

export interface UseSimLabAutoRepOptions {
  /** Latest matching event from `useVisionEvents` (already filtered). */
  lastEvent: EventEnvelope | null;
  /** Called exactly once per new FORMATION_LOCKED event_id. */
  onRep: (event: EventEnvelope) => void;
}

export function useSimLabAutoRep({ lastEvent, onRep }: UseSimLabAutoRepOptions): void {
  // event_id of the last event that counted a rep — the dedupe key.
  const lastRepEventId = useRef<string | null>(null);
  // Keep the latest onRep without making it an effect dependency (so a new
  // callback identity each render doesn't refire the rep).
  const onRepRef = useRef(onRep);
  onRepRef.current = onRep;

  useEffect(() => {
    if (!lastEvent) return;
    // Defensive: the hook filters upstream, but never count a non-formation
    // event as a rep.
    if (lastEvent.event_type !== 'FORMATION_LOCKED') return;
    // Dedupe: a re-surfaced event_id (re-render / reconnect replay) is a no-op.
    if (lastEvent.event_id === lastRepEventId.current) return;
    lastRepEventId.current = lastEvent.event_id;
    onRepRef.current(lastEvent);
  }, [lastEvent]);
}

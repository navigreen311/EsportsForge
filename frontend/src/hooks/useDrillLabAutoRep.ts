/**
 * useDrillLabAutoRep — Phase 1a Day 3.
 *
 * Maps vision events to drill reps: one `FORMATION_LOCKED` (which fires once
 * per play-call screen, ADR 0015 / §4c) → exactly one rep. Deduped by
 * `event_id` so a re-surfaced event (React re-render, or a reconnect that
 * replays the latest event as a fresh object) never double-counts.
 *
 * This is the Day-3 rep-counting boundary deliberately kept OUT of the Day-2
 * `useVisionEvents` hook (which stays counting-agnostic). The actual counter
 * lives in `useDrills` (`completeRep`); this unit just fires `onRep` once per
 * new formation event. Event-display-only — no coaching (Phase 1b).
 */
import { useEffect, useRef } from 'react';

import type { EventEnvelope } from './useVisionEvents';

export interface UseDrillLabAutoRepOptions {
  /** Latest matching event from `useVisionEvents` (already filtered). */
  lastEvent: EventEnvelope | null;
  /** Called exactly once per new FORMATION_LOCKED event_id. */
  onRep: (event: EventEnvelope) => void;
}

export function useDrillLabAutoRep({ lastEvent, onRep }: UseDrillLabAutoRepOptions): void {
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

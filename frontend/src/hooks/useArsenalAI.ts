/**
 * useArsenalAI — surfaces the latest /arsenal/trigger weapon recommendation.
 *
 * Two drivers (Phase 1c):
 *   - Manual fallback: polls /arsenal/trigger every 2 min while the player is
 *     in-game (session.playing, coaching not paused) — the pre-vision behaviour.
 *   - Event-driven: when arsenalVisionEnabled, provisions a broker session and
 *     subscribes to COVERAGE_LOCKED; a live coverage is merged into game_state
 *     (defensiveCoverage) and fires the trigger IMMEDIATELY, once per new coverage.
 *
 * Vision-active counts as "playing" (effectivePlaying) so the trigger fires + shows
 * off a live coverage even if the app session flag isn't set. Return signature is
 * unchanged — ArsenalAlert (the only consumer) needs no change.
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import api from '@/lib/api';
import { useSessionStore } from '@/lib/sessionStore';
import { useActiveArsenalTitle } from '@/hooks/useArsenal';
import { useGameState } from '@/lib/arsenal/gameStateStore';
import { arsenalVisionEnabled } from '@/lib/vafFlags';
import { useVisionEvents } from '@/hooks/useVisionEvents';
import { useCoverageGameState } from '@/hooks/useCoverageGameState';

export interface TriggerResult {
  trigger: boolean;
  reason?: string;
  urgency?: 'now' | 'soon' | 'watch';
  timing?: string;
  weapon_id?: string;
  weapon?: {
    id: string;
    name: string;
    category: string;
    title_id: string;
  };
}

const POLL_MS = 2 * 60 * 1000;

export function useArsenalAI() {
  const session = useSessionStore((s) => s.session);
  const titleId = useActiveArsenalTitle();
  const gameState = useGameState(titleId);
  const [last, setLast] = useState<TriggerResult>({ trigger: false });
  const [dismissedFor, setDismissedFor] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);
  const inFlight = useRef(false);

  const playing = !!session?.playing && !session.coachingPaused;

  // Phase 1c live-vision: provision a broker session while the flag is on, then
  // subscribe to COVERAGE_LOCKED. Vision-active is treated as "playing".
  const vafFlagOn = arsenalVisionEnabled();
  const [vafSession, setVafSession] = useState<{ sessionId: string; token: string } | null>(null);
  useEffect(() => {
    if (!vafFlagOn) return;
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.post('/visionaudio/sessions/start');
        if (!cancelled) setVafSession({ sessionId: data.session_id, token: data.token });
      } catch {
        // Broker unavailable / disabled server-side — stays on the manual poll.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [vafFlagOn]);
  const { lastEvent: coverageEvent } = useVisionEvents({
    sessionId: vafSession?.sessionId ?? null,
    token: vafSession?.token ?? null,
    eventType: 'COVERAGE_LOCKED',
    enabled: vafFlagOn && !!vafSession,
  });
  const liveCoverage = useRef<string | null>(null);
  const visionActive = vafFlagOn && !!vafSession;
  const effectivePlaying = playing || visionActive;

  const poll = async () => {
    if (inFlight.current) return;
    if (!effectivePlaying) return;
    // Vision-driven mode: do NOT fire a blind trigger before a coverage exists — it
    // returns trigger:false and clobbers a live coverage-driven trigger:true via setLast
    // (the "card never shows" race, live-diagnosed 2026-07-16). Coverage events drive it.
    if (visionActive && !liveCoverage.current) return;
    inFlight.current = true;
    try {
      // Merge the live detected coverage into game_state so the trigger weighs it.
      // The backend game_state is free-form, so no schema change is needed.
      const gs = liveCoverage.current
        ? { ...gameState, defensiveCoverage: liveCoverage.current }
        : gameState;
      const { data } = await api.post<TriggerResult>('/arsenal/trigger', {
        title_id: titleId,
        game_state: gs,
        session_id: session?.startTime?.toString(),
      });
      setLast(data);
    } catch {
      // silent — retry on next interval / next coverage
    } finally {
      inFlight.current = false;
    }
  };

  // Event-driven: a NEW COVERAGE_LOCKED updates the coverage + fires the trigger now.
  // (The bridge dedupes by event_id; onCoverage calls the latest poll via its ref.)
  useCoverageGameState({
    lastEvent: coverageEvent,
    onCoverage: (s) => {
      liveCoverage.current = s.coverage;
      void poll();
    },
  });

  useEffect(() => {
    if (!effectivePlaying) {
      if (timerRef.current) {
        window.clearInterval(timerRef.current);
        timerRef.current = null;
      }
      return;
    }
    poll();
    timerRef.current = window.setInterval(poll, POLL_MS);
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
      timerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectivePlaying, titleId]);

  const dismiss = () => {
    if (last.weapon_id) setDismissedFor(last.weapon_id);
  };

  const visible =
    effectivePlaying &&
    last.trigger === true &&
    last.weapon_id !== undefined &&
    last.weapon_id !== dismissedFor;

  return { last, visible, dismiss, refetch: poll };
}

/**
 * useArsenalAI — polls /arsenal/trigger every 2 minutes while the player
 * is in-game (and coaching is not paused), exposes the latest trigger.
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import api from '@/lib/api';
import { useSessionStore } from '@/lib/sessionStore';
import {
  useActiveArsenalTitle,
} from '@/hooks/useArsenal';
import { useGameState } from '@/lib/arsenal/gameStateStore';

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

  const poll = async () => {
    if (inFlight.current) return;
    if (!playing) return;
    inFlight.current = true;
    try {
      const { data } = await api.post<TriggerResult>('/arsenal/trigger', {
        title_id: titleId,
        game_state: gameState,
        session_id: session?.startTime?.toString(),
      });
      setLast(data);
    } catch {
      // silent — retry on next interval
    } finally {
      inFlight.current = false;
    }
  };

  useEffect(() => {
    if (!playing) {
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
  }, [playing, titleId]);

  const dismiss = () => {
    if (last.weapon_id) setDismissedFor(last.weapon_id);
  };

  const visible =
    playing &&
    last.trigger === true &&
    last.weapon_id !== undefined &&
    last.weapon_id !== dismissedFor;

  return { last, visible, dismiss, refetch: poll };
}

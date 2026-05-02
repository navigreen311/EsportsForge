/**
 * Session store — tracks the active player session (mode, start time, opponent),
 * persists to sessionStorage so the timer survives client-side navigation.
 */

'use client';

import { useEffect, useState } from 'react';
import { create } from 'zustand';
import type { GameMode } from './store';

const STORAGE_KEY = 'esportsforge_active_session';

export interface ActiveSession {
  mode: GameMode;
  startTime: number; // ms epoch
  opponent?: string;
  drillId?: string;
}

interface SessionState {
  session: ActiveSession | null;
  hydrated: boolean;
  startSession: (mode: GameMode, extra?: Partial<Omit<ActiveSession, 'mode' | 'startTime'>>) => void;
  endSession: () => void;
  hydrate: () => void;
}

function readStorage(): ActiveSession | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as ActiveSession;
    if (typeof parsed?.startTime !== 'number' || !parsed.mode) return null;
    return parsed;
  } catch {
    return null;
  }
}

function writeStorage(session: ActiveSession | null) {
  if (typeof window === 'undefined') return;
  if (session) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  else sessionStorage.removeItem(STORAGE_KEY);
}

export const useSessionStore = create<SessionState>((set) => ({
  session: null,
  hydrated: false,
  startSession: (mode, extra) => {
    const session: ActiveSession = {
      mode,
      startTime: Date.now(),
      ...extra,
    };
    writeStorage(session);
    set({ session, hydrated: true });
  },
  endSession: () => {
    writeStorage(null);
    set({ session: null });
  },
  hydrate: () => {
    set({ session: readStorage(), hydrated: true });
  },
}));

/** Live elapsed-time string (mm:ss or h:mm:ss) for the active session. */
export function useSessionElapsed(session: ActiveSession | null): string {
  const [now, setNow] = useState<number>(() => Date.now());

  useEffect(() => {
    if (!session) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [session]);

  if (!session) return '0:00';
  const seconds = Math.max(0, Math.floor((now - session.startTime) / 1000));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

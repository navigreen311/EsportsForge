/**
 * Session store — tracks the active player session (mode, opponent, steps,
 * in-game sub-state, per-session game results) and persists to sessionStorage
 * so timers and progress survive client-side navigation.
 */

'use client';

import { useEffect, useState } from 'react';
import { create } from 'zustand';
import type { GameMode } from './store';

const STORAGE_KEY = 'esportsforge_active_session';

export type StepKey = 'warRoom' | 'gameplan' | 'playing' | 'logged';

export interface SessionStep {
  key: StepKey;
  done: boolean;
}

export interface SessionGameResult {
  outcome: 'won' | 'lost' | 'mixed';
  myScore: number;
  theirScore: number;
  killShotWorked: 'yes' | 'partly' | 'no';
  note: string;
  loggedAt: number;
}

export interface ActiveSession {
  mode: GameMode;
  startTime: number; // ms epoch — total session start
  opponent?: string;
  drillId?: string;

  // Step progress (auto-updated by route changes / explicit actions)
  steps: Record<StepKey, boolean>;

  // In-game sub-state ("I'm In Game" pressed)
  playing: boolean;
  playingStartedAt: number | null;
  coachingPaused: boolean;

  // Post-game state
  gameCount: number;
  results: SessionGameResult[];
}

interface SessionState {
  session: ActiveSession | null;
  hydrated: boolean;
  startSession: (
    mode: GameMode,
    extra?: Partial<Pick<ActiveSession, 'opponent' | 'drillId'>>
  ) => void;
  endSession: () => void;
  hydrate: () => void;

  markStep: (key: StepKey, done?: boolean) => void;

  // In-game sub-state
  startPlaying: () => void;
  stopPlaying: () => void;
  toggleCoachingPaused: () => void;

  // Post-game
  recordResult: (result: SessionGameResult) => void;
  startNextGame: () => void;
}

function readStorage(): ActiveSession | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<ActiveSession>;
    if (typeof parsed?.startTime !== 'number' || !parsed.mode) return null;
    return normaliseSession(parsed);
  } catch {
    return null;
  }
}

function normaliseSession(s: Partial<ActiveSession>): ActiveSession {
  return {
    mode: s.mode!,
    startTime: s.startTime!,
    opponent: s.opponent,
    drillId: s.drillId,
    steps: {
      warRoom: s.steps?.warRoom ?? false,
      gameplan: s.steps?.gameplan ?? false,
      playing: s.steps?.playing ?? false,
      logged: s.steps?.logged ?? false,
    },
    playing: s.playing ?? false,
    playingStartedAt: s.playingStartedAt ?? null,
    coachingPaused: s.coachingPaused ?? false,
    gameCount: s.gameCount ?? 0,
    results: s.results ?? [],
  };
}

function writeStorage(session: ActiveSession | null) {
  if (typeof window === 'undefined') return;
  if (session) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  else sessionStorage.removeItem(STORAGE_KEY);
}

export const useSessionStore = create<SessionState>((set, get) => ({
  session: null,
  hydrated: false,

  startSession: (mode, extra) => {
    const session = normaliseSession({
      mode,
      startTime: Date.now(),
      opponent: extra?.opponent,
      drillId: extra?.drillId,
    });
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

  markStep: (key, done = true) => {
    const cur = get().session;
    if (!cur) return;
    if (cur.steps[key] === done) return;
    const next: ActiveSession = {
      ...cur,
      steps: { ...cur.steps, [key]: done },
    };
    writeStorage(next);
    set({ session: next });
  },

  startPlaying: () => {
    const cur = get().session;
    if (!cur) return;
    const next: ActiveSession = {
      ...cur,
      playing: true,
      playingStartedAt: Date.now(),
      coachingPaused: false,
      steps: { ...cur.steps, playing: true },
    };
    writeStorage(next);
    set({ session: next });
  },

  stopPlaying: () => {
    const cur = get().session;
    if (!cur) return;
    const next: ActiveSession = {
      ...cur,
      playing: false,
      playingStartedAt: null,
    };
    writeStorage(next);
    set({ session: next });
  },

  toggleCoachingPaused: () => {
    const cur = get().session;
    if (!cur) return;
    const next: ActiveSession = { ...cur, coachingPaused: !cur.coachingPaused };
    writeStorage(next);
    set({ session: next });
  },

  recordResult: (result) => {
    const cur = get().session;
    if (!cur) return;
    const next: ActiveSession = {
      ...cur,
      results: [...cur.results, result],
      gameCount: cur.gameCount + 1,
      steps: { ...cur.steps, logged: true },
    };
    writeStorage(next);
    set({ session: next });
  },

  startNextGame: () => {
    const cur = get().session;
    if (!cur) return;
    const next: ActiveSession = {
      ...cur,
      playing: false,
      playingStartedAt: null,
      coachingPaused: false,
      steps: { ...cur.steps, playing: false, logged: false },
    };
    writeStorage(next);
    set({ session: next });
  },
}));

/** Live elapsed-time string (mm:ss or h:mm:ss) for a given anchor timestamp. */
export function useElapsed(anchorMs: number | null | undefined): string {
  const [now, setNow] = useState<number>(() => Date.now());

  useEffect(() => {
    if (!anchorMs) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [anchorMs]);

  if (!anchorMs) return '0:00';
  const seconds = Math.max(0, Math.floor((now - anchorMs) / 1000));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

/** Backwards-compatible wrapper for the existing call site. */
export function useSessionElapsed(session: ActiveSession | null): string {
  return useElapsed(session?.startTime ?? null);
}

/** Total session duration in seconds (for the summary). */
export function sessionDurationSeconds(session: ActiveSession): number {
  return Math.max(0, Math.floor((Date.now() - session.startTime) / 1000));
}

// ---------------------------------------------------------------------------
// Session UI store — cross-page signals for modal orchestration
// ---------------------------------------------------------------------------

interface SessionUIState {
  /** "End Session" was requested somewhere in the app — show the summary. */
  endRequested: boolean;
  requestEnd: () => void;
  clearEnd: () => void;
}

export const useSessionUIStore = create<SessionUIState>((set) => ({
  endRequested: false,
  requestEnd: () => set({ endRequested: true }),
  clearEnd: () => set({ endRequested: false }),
}));


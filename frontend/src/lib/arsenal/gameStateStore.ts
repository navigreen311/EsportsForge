/**
 * Per-title game state — manually-entered for now (full overlay/vision
 * integration lands later). Persisted to sessionStorage so it survives
 * page navigation during a session.
 */

'use client';

import { useEffect, useState } from 'react';
import { create } from 'zustand';
import type { ArsenalTitleId } from '@/lib/arsenal/titleMeta';

type GameState = Record<string, unknown>;
type AllStates = Record<ArsenalTitleId, GameState>;

const KEY = 'esportsforge_arsenal_game_state';

function load(): AllStates {
  if (typeof window === 'undefined') return {} as AllStates;
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return {} as AllStates;
    return JSON.parse(raw) as AllStates;
  } catch {
    return {} as AllStates;
  }
}

function save(state: AllStates) {
  if (typeof window === 'undefined') return;
  sessionStorage.setItem(KEY, JSON.stringify(state));
}

interface State {
  states: AllStates;
  hydrated: boolean;
  hydrate: () => void;
  set: (titleId: ArsenalTitleId, patch: GameState) => void;
  clear: (titleId: ArsenalTitleId) => void;
}

export const useGameStateStore = create<State>((setStore, get) => ({
  states: {} as AllStates,
  hydrated: false,
  hydrate: () => {
    setStore({ states: load(), hydrated: true });
  },
  set: (titleId, patch) => {
    const next = {
      ...get().states,
      [titleId]: { ...(get().states[titleId] ?? {}), ...patch },
    };
    save(next);
    setStore({ states: next });
  },
  clear: (titleId) => {
    const next = { ...get().states };
    delete next[titleId];
    save(next);
    setStore({ states: next });
  },
}));

export function useGameState(titleId: ArsenalTitleId): GameState {
  const states = useGameStateStore((s) => s.states);
  const hydrated = useGameStateStore((s) => s.hydrated);
  const hydrate = useGameStateStore((s) => s.hydrate);
  const [first, setFirst] = useState(true);

  useEffect(() => {
    if (!hydrated) hydrate();
    setFirst(false);
  }, [hydrated, hydrate]);

  if (first && !hydrated) return {};
  return states[titleId] ?? {};
}

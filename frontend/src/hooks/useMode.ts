/**
 * Hook for current game mode state.
 * Wraps the Zustand store for mode selection.
 */

"use client";

import { useUIStore, MODE_CONFIG } from '@/lib/store';
import type { GameMode } from '@/lib/store';

export function useMode() {
  const currentMode = useUIStore((s) => s.currentMode);
  const setMode = useUIStore((s) => s.setMode);

  const modeConfig = MODE_CONFIG[currentMode];
  const allModes = Object.entries(MODE_CONFIG).map(([id, config]) => ({
    id: id as GameMode,
    ...config,
  }));

  return {
    currentMode,
    modeConfig,
    allModes,
    setMode,
  };
}

export type { GameMode };

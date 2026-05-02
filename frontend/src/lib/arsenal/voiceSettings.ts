/**
 * Arsenal voice coaching settings — persisted in localStorage so the
 * server-side settings UI can stay synchronous with the client. (Move
 * to identityProfile.arsenalVoiceSettings in a follow-up patch.)
 */

'use client';

import { useEffect, useState } from 'react';
import { create } from 'zustand';

export type CoachTone = 'intense' | 'standard' | 'calm';

export interface ArsenalVoiceSettings {
  enabled: boolean;
  guidedPractice: boolean;
  postDebrief: boolean;
  preExecBrief: boolean;
  tone: CoachTone;
}

const KEY = 'esportsforge_arsenal_voice_settings';

const DEFAULTS: ArsenalVoiceSettings = {
  enabled: true,
  guidedPractice: true,
  postDebrief: true,
  preExecBrief: true,
  tone: 'standard',
};

function load(): ArsenalVoiceSettings {
  if (typeof window === 'undefined') return DEFAULTS;
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return DEFAULTS;
    return { ...DEFAULTS, ...(JSON.parse(raw) as Partial<ArsenalVoiceSettings>) };
  } catch {
    return DEFAULTS;
  }
}

function save(s: ArsenalVoiceSettings) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(KEY, JSON.stringify(s));
}

interface State {
  settings: ArsenalVoiceSettings;
  hydrated: boolean;
  hydrate: () => void;
  update: (patch: Partial<ArsenalVoiceSettings>) => void;
  reset: () => void;
}

export const useArsenalVoiceSettings = create<State>((set, get) => ({
  settings: DEFAULTS,
  hydrated: false,
  hydrate: () => set({ settings: load(), hydrated: true }),
  update: (patch) => {
    const next = { ...get().settings, ...patch };
    save(next);
    set({ settings: next });
  },
  reset: () => {
    save(DEFAULTS);
    set({ settings: DEFAULTS });
  },
}));

/** SSR-safe accessor that hydrates on first mount. */
export function useArsenalVoice(): ArsenalVoiceSettings {
  const { settings, hydrated, hydrate } = useArsenalVoiceSettings();
  const [first, setFirst] = useState(true);
  useEffect(() => {
    if (!hydrated) hydrate();
    setFirst(false);
  }, [hydrated, hydrate]);
  if (first && !hydrated) return DEFAULTS;
  return settings;
}

/** Tone -> SpeechSynthesis rate. Calm slower, Intense faster. */
export function toneSpeed(tone: CoachTone): number {
  if (tone === 'intense') return 1.15;
  if (tone === 'calm') return 0.9;
  return 1.0;
}

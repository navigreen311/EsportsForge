/**
 * Arsenal voice coaching settings.
 *
 * Settings are persisted on the server (IdentityProfile.arsenal_voice_settings)
 * via React Query. On first load, if the server returns nothing and there are
 * legacy settings in localStorage, they are migrated up automatically.
 *
 * Also exports voice-resolution helpers used by VoiceForgeService so each
 * coaching tone maps to a distinct browser voice, not just a different rate.
 */

'use client';

import { useEffect } from 'react';
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import api from '@/lib/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type CoachTone = 'intense' | 'standard' | 'calm';

export interface ArsenalVoiceSettings {
  enabled: boolean;
  guidedPractice: boolean;
  postDebrief: boolean;
  preExecBrief: boolean;
  tone: CoachTone;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const LEGACY_LS_KEY = 'esportsforge_arsenal_voice_settings';
const VOICE_CACHE_KEY = 'esportsforge_voice_uris';
const QUERY_KEY = ['arsenal-voice-settings'] as const;

const DEFAULTS: ArsenalVoiceSettings = {
  enabled: true,
  guidedPractice: true,
  postDebrief: true,
  preExecBrief: true,
  tone: 'standard',
};

// ---------------------------------------------------------------------------
// Voice resolution helpers (Task A)
// ---------------------------------------------------------------------------

/**
 * Ranked voice name candidates per coaching tone.
 * The first match found in the browser's voice list wins.
 */
const TONE_VOICE_NAMES: Record<CoachTone, string[]> = {
  intense: ['Daniel', 'Aaron', 'Microsoft David', 'Google US English'],
  standard: ['Samantha', 'Microsoft Zira', 'Google US English', 'Alex'],
  calm: ['Karen', 'Microsoft Eva', 'Moira', 'Victoria'],
};

const TONE_RATES: Record<CoachTone, number> = {
  intense: 1.15,
  standard: 1.0,
  calm: 0.9,
};

export interface ResolvedVoice {
  voiceURI: string | null;
  rate: number;
}

function loadVoiceCache(): Record<CoachTone, string | null> | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(VOICE_CACHE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveVoiceCache(cache: Record<CoachTone, string | null>): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(VOICE_CACHE_KEY, JSON.stringify(cache));
  } catch {
    // Non-critical.
  }
}

/**
 * Resolve and cache one voiceURI per coaching tone from the browser's
 * SpeechSynthesis voice list. Falls back to null (caller uses default voice).
 *
 * Safe to call multiple times — results are cached in localStorage so
 * re-ranking doesn't happen on every utterance.
 */
export function resolveVoiceURIs(): Record<CoachTone, string | null> {
  if (typeof window === 'undefined') {
    return { intense: null, standard: null, calm: null };
  }

  const cached = loadVoiceCache();
  if (cached) return cached;

  const synth = window.speechSynthesis;
  if (!synth) return { intense: null, standard: null, calm: null };

  const voices = synth.getVoices();
  if (!voices.length) return { intense: null, standard: null, calm: null };

  const result: Record<CoachTone, string | null> = {
    intense: null,
    standard: null,
    calm: null,
  };

  const tones: CoachTone[] = ['intense', 'standard', 'calm'];
  for (const tone of tones) {
    for (const candidate of TONE_VOICE_NAMES[tone]) {
      const match = voices.find(
        (v) => v.name === candidate || v.name.includes(candidate)
      );
      if (match) {
        result[tone] = match.voiceURI;
        break;
      }
    }
    // Fall back to first en-US voice if no named match.
    if (!result[tone]) {
      result[tone] = voices.find((v) => v.lang === 'en-US')?.voiceURI ?? null;
    }
  }

  saveVoiceCache(result);
  return result;
}

/**
 * Set up the onvoiceschanged listener so the cache is rebuilt when the
 * browser finishes loading its voice list (Chrome loads voices async).
 * Call once on app mount.
 */
export function registerVoicesChangedListener(): () => void {
  if (typeof window === 'undefined') return () => {};
  const synth = window.speechSynthesis;
  if (!synth) return () => {};

  const handler = () => {
    // Bust the cache so the next resolution picks up the full voice list.
    try {
      localStorage.removeItem(VOICE_CACHE_KEY);
    } catch {
      // Ignore.
    }
    resolveVoiceURIs();
  };

  synth.onvoiceschanged = handler;
  return () => {
    if (synth.onvoiceschanged === handler) synth.onvoiceschanged = null;
  };
}

/**
 * Return the resolved voice for a given coaching tone.
 */
export function resolveVoiceForTone(tone: CoachTone): ResolvedVoice {
  const uris = resolveVoiceURIs();
  return { voiceURI: uris[tone] ?? null, rate: TONE_RATES[tone] };
}

// ---------------------------------------------------------------------------
// Deprecated helper (kept for call sites in older code)
// ---------------------------------------------------------------------------

/**
 * @deprecated Pass `tone` directly to VoiceForgeService.speak / speakAsync
 * instead of computing the rate here. This function will be removed in a
 * future release.
 */
export function toneSpeed(tone: CoachTone): number {
  return TONE_RATES[tone];
}

// ---------------------------------------------------------------------------
// Legacy localStorage helpers (used for migration shim only)
// ---------------------------------------------------------------------------

function loadLegacySettings(): Partial<ArsenalVoiceSettings> | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(LEGACY_LS_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as Partial<ArsenalVoiceSettings>;
  } catch {
    return null;
  }
}

function clearLegacySettings(): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.removeItem(LEGACY_LS_KEY);
  } catch {
    // Ignore.
  }
}

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function fetchSettings(): Promise<ArsenalVoiceSettings> {
  const { data } = await api.get<ArsenalVoiceSettings>(
    '/users/me/arsenal-voice-settings'
  );
  return data;
}

async function patchSettings(
  patch: Partial<ArsenalVoiceSettings>
): Promise<ArsenalVoiceSettings> {
  const { data } = await api.patch<ArsenalVoiceSettings>(
    '/users/me/arsenal-voice-settings',
    patch
  );
  return data;
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

/**
 * Returns the current Arsenal voice settings from the server.
 * Falls back to defaults while loading or unauthenticated.
 */
export function useArsenalVoice(): ArsenalVoiceSettings {
  const queryClient = useQueryClient();

  const { data } = useQuery<ArsenalVoiceSettings>({
    queryKey: QUERY_KEY,
    queryFn: fetchSettings,
    placeholderData: DEFAULTS,
    staleTime: 60_000,
    retry: 1,
  });

  // Migration shim: if server returned empty and localStorage has legacy data,
  // patch it up once and clear the legacy key.
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const legacy = loadLegacySettings();
    if (!legacy) return;
    // If the server already has non-default settings, skip migration.
    const current = queryClient.getQueryData<ArsenalVoiceSettings>(QUERY_KEY);
    const isServerEmpty =
      !current ||
      (current.enabled === DEFAULTS.enabled &&
        current.tone === DEFAULTS.tone);
    if (!isServerEmpty) {
      clearLegacySettings();
      return;
    }
    patchSettings(legacy)
      .then((updated) => {
        queryClient.setQueryData(QUERY_KEY, updated);
        clearLegacySettings();
      })
      .catch(() => {
        // Best-effort — non-fatal.
      });
  // Run once on mount only.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return data ?? DEFAULTS;
}

/**
 * Returns a stable `update` function that PATCHes the server with a partial
 * settings object and updates the React Query cache optimistically.
 */
export function useArsenalVoiceSettings(): {
  update: (patch: Partial<ArsenalVoiceSettings>) => void;
} {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    ArsenalVoiceSettings,
    unknown,
    Partial<ArsenalVoiceSettings>
  >({
    mutationFn: patchSettings,
    onMutate: async (patch) => {
      await queryClient.cancelQueries({ queryKey: QUERY_KEY });
      const previous =
        queryClient.getQueryData<ArsenalVoiceSettings>(QUERY_KEY) ?? DEFAULTS;
      queryClient.setQueryData<ArsenalVoiceSettings>(QUERY_KEY, {
        ...previous,
        ...patch,
      });
      return { previous };
    },
    onError: (_err, _patch, context) => {
      const ctx = context as { previous?: ArsenalVoiceSettings } | undefined;
      if (ctx?.previous) {
        queryClient.setQueryData(QUERY_KEY, ctx.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  return { update: (patch) => mutation.mutate(patch) };
}

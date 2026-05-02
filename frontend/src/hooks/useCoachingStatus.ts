/**
 * Aggregates real-ish status of the three coaching subsystems: VoiceForge
 * (voice availability via Web Speech API), ForgeCore (always available
 * as long as we have an API base), and TiltGuard (mood + warning level).
 *
 * Returns ready-to-render labels and dot tones so the UI doesn't have to
 * re-derive them at every call site.
 */

'use client';

import { useEffect, useState } from 'react';
import { VoiceForgeService } from '@/lib/services/voiceforge';
import { loadStoredMood } from '@/components/dashboard/TiltGuardCheckin';
import type { TiltGuardMood } from '@/types/dashboard';
import { useSessionStore } from '@/lib/sessionStore';

export type DotTone = 'green' | 'amber' | 'red';

export interface SubsystemStatus {
  label: string;
  detail: string;
  tone: DotTone;
}

export interface CoachingStatus {
  voice: SubsystemStatus;
  forgeCore: SubsystemStatus;
  tiltGuard: SubsystemStatus;
}

function moodWarning(mood: TiltGuardMood | null): DotTone {
  if (!mood) return 'amber';
  if (mood === 'tilted') return 'red';
  if (mood === 'frustrated' || mood === 'tired') return 'amber';
  return 'green';
}

function moodLabel(mood: TiltGuardMood | null): string {
  if (!mood) return 'No mood logged today';
  return (
    {
      'locked-in': 'Locked In',
      good: 'Good',
      tired: 'Tired',
      frustrated: 'Frustrated',
      tilted: 'Tilted',
    } as const
  )[mood];
}

export function useCoachingStatus(): CoachingStatus {
  const [voiceAvailable, setVoiceAvailable] = useState(false);
  const [mood, setMood] = useState<TiltGuardMood | null>(null);
  const session = useSessionStore((s) => s.session);
  const playing = !!session?.playing;
  const coachingPaused = !!session?.coachingPaused;

  useEffect(() => {
    setVoiceAvailable(VoiceForgeService.isAvailable());
    setMood(loadStoredMood());
  }, []);

  const voice: SubsystemStatus = voiceAvailable
    ? coachingPaused && playing
      ? {
          label: 'VoiceForge: Paused',
          detail: 'Coaching paused — resume when you are ready',
          tone: 'amber',
        }
      : playing
      ? {
          label: 'VoiceForge: Active',
          detail: 'Say "read play", "next drill", or "war room"',
          tone: 'green',
        }
      : {
          label: 'VoiceForge: Standing by',
          detail: 'Activates when you hit "I\'m In Game"',
          tone: 'green',
        }
    : {
        label: 'VoiceForge: Offline',
        detail: 'Voice coaching unavailable — check VoiceForge',
        tone: 'red',
      };

  const forgeCore: SubsystemStatus = playing
    ? {
        label: 'ForgeCore: Watching',
        detail: 'Coaching cues ready — ask anything',
        tone: 'green',
      }
    : {
        label: 'ForgeCore: Ready',
        detail: 'Recommendations loaded for this opponent',
        tone: 'green',
      };

  const tiltTone = moodWarning(mood);
  const tiltGuard: SubsystemStatus = {
    label: tiltTone === 'green' ? 'TiltGuard: Monitoring' : 'TiltGuard: Watch',
    detail:
      tiltTone === 'green'
        ? `Mood: ${moodLabel(mood)} — performance tracking active`
        : tiltTone === 'amber'
        ? `Mood: ${moodLabel(mood)} — consider a 5-min reset`
        : `Mood: ${moodLabel(mood)} — step away before queuing`,
    tone: tiltTone,
  };

  return { voice, forgeCore, tiltGuard };
}

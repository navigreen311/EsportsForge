'use client';

import { useEffect, useRef } from 'react';
import { VoiceForgeService } from '@/lib/services/voiceforge';

interface TiltGuardVoiceCheckInProps {
  onMoodDetected: (mood: string) => void;
}

const MOOD_KEYWORDS = ['locked in', 'good', 'tired', 'frustrated', 'tilted'] as const;

const TILT_MOODS = new Set(['tilted', 'frustrated']);

export default function TiltGuardVoiceCheckIn({
  onMoodDetected,
}: TiltGuardVoiceCheckInProps) {
  const hasRun = useRef(false);

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    if (!VoiceForgeService.isAvailable()) return;

    const run = async () => {
      VoiceForgeService.speak(
        'How are you feeling? Say: Locked in, Good, Tired, Frustrated, or Tilted.',
      );

      const transcript = await VoiceForgeService.listen({ timeout: 5000 });

      if (!transcript) return;

      const lower = transcript.toLowerCase();
      const matched = MOOD_KEYWORDS.find((keyword) => lower.includes(keyword));

      if (!matched) return;

      if (TILT_MOODS.has(matched)) {
        VoiceForgeService.speak(
          'TiltGuard activated. I\'ll monitor for performance drops.',
        );
      } else {
        VoiceForgeService.speak(`Got it, ${matched}. Let's get to work.`);
      }

      onMoodDetected(matched);
    };

    run();
  }, [onMoodDetected]);

  return null;
}

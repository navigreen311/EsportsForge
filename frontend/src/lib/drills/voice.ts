/**
 * VoiceForge phrasing for the active drill flow. Centralised so the rep
 * counter, the modal, and the debrief all draw from the same script.
 *
 * Speech is fire-and-forget. VoiceForgeService no-ops when speech synthesis
 * is unavailable (SSR, NEXT_PUBLIC_VOICEFORGE_ENABLED=false, denied perms),
 * so callers don't need to guard.
 */

import { VoiceForgeService } from '@/lib/services/voiceforge';

export function speakBrief(drillName: string, objective: string): void {
  VoiceForgeService.speak(
    `Starting ${drillName}. ${objective} VisionAudioForge is watching. Go to your game.`,
    { interruptCurrent: true },
  );
}

export function speakRepResult(args: {
  success: boolean;
  repNumber: number;
  totalReps: number;
}): void {
  const tail = `Rep ${args.repNumber} of ${args.totalReps}.`;
  const line = args.success
    ? `Good rep. ${tail} Keep going.`
    : `Missed that one. ${tail} Reset and reload.`;
  VoiceForgeService.speak(line, { interruptCurrent: true });
}

/** Mid-session and near-end progress cues, queued after the rep result. */
export function speakProgressCue(args: {
  repNumber: number;
  totalReps: number;
}): void {
  const remaining = args.totalReps - args.repNumber;
  const halfway = Math.ceil(args.totalReps / 2);
  if (args.repNumber === halfway && args.totalReps >= 4) {
    VoiceForgeService.speak(
      `Halfway there. ${args.repNumber} of ${args.totalReps}. Stay focused.`,
    );
    return;
  }
  if (remaining === 2 && args.totalReps >= 4) {
    VoiceForgeService.speak('Two reps left. Make them count.');
  }
}

export function speakDebrief(args: {
  drillName: string;
  successReps: number;
  totalReps: number;
  insight: string;
}): void {
  VoiceForgeService.speak(
    `${args.drillName} complete. ${args.successReps} of ${args.totalReps} successful. ${args.insight}`,
    { interruptCurrent: true },
  );
}

export function stopSpeech(): void {
  VoiceForgeService.stop();
}

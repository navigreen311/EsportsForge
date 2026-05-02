/**
 * Competition Mode card — replaces the idle "Start Session" card on the
 * dashboard while a session is active. Shows current opponent, ForgeCore
 * recommendation, primary kill-shot actions, "I'm In Game" coaching trigger,
 * and live coaching subsystem status.
 */

'use client';

import { useRouter } from 'next/navigation';
import {
  Gamepad2,
  Target,
  ClipboardList,
  Brain,
  StickyNote,
  Play,
  Pause,
  CheckCircle2,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useSessionStore, useElapsed } from '@/lib/sessionStore';
import { useCoachingStatus } from '@/hooks/useCoachingStatus';
import { useUIStore } from '@/lib/store';
import { TIER_CONFIG } from '@/lib/store';
import { CoachingStatusRow } from './CoachingStatus';
import { ArsenalAlert } from './ArsenalAlert';
import { VoiceForgeService } from '@/lib/services/voiceforge';
import { useDashboard } from '@/hooks/useDashboard';

interface CompetitionModeCardProps {
  onLogResult: () => void;
  onMentalReset: () => void;
}

export function CompetitionModeCard({
  onLogResult,
  onMentalReset,
}: CompetitionModeCardProps) {
  const session = useSessionStore((s) => s.session);
  const startPlaying = useSessionStore((s) => s.startPlaying);
  const stopPlaying = useSessionStore((s) => s.stopPlaying);
  const toggleCoachingPaused = useSessionStore((s) => s.toggleCoachingPaused);
  const inGameElapsed = useElapsed(session?.playingStartedAt ?? null);
  const sessionElapsed = useElapsed(session?.startTime ?? null);
  const coaching = useCoachingStatus();
  const userTier = useUIStore((s) => s.userTier);
  const tier = TIER_CONFIG[userTier];
  const router = useRouter();
  const { data } = useDashboard();

  if (!session) return null;

  const opponent = session.opponent ?? 'Next Opponent';
  const headlineRec =
    data.priority?.weakness && data.priority?.confidence
      ? `Focus your kill shot on: ${data.priority.weakness}. Confidence: ${data.priority.confidence}%.`
      : 'Run your top kill-shot play on the opening drive — confidence is high.';

  const handleStartPlaying = () => {
    startPlaying();
    VoiceForgeService.speak(
      `ForgeCore is with you. Say "read play" for your kill shot. Good luck.`,
      { interruptCurrent: true }
    );
  };

  const handleStopPlaying = () => {
    stopPlaying();
    VoiceForgeService.stop();
    onLogResult();
  };

  const handleTogglePause = () => {
    toggleCoachingPaused();
    if (session.coachingPaused) {
      VoiceForgeService.speak('Coaching resumed.', { interruptCurrent: true });
    } else {
      VoiceForgeService.stop();
    }
  };

  return (
    <div className="overflow-hidden rounded-xl border border-forge-500/30 bg-emerald-950/20 shadow-lg">
      {/* Header strip */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-forge-500/20 bg-emerald-950/40 px-5 py-3">
        <span className="flex items-center gap-2 text-sm font-bold text-dark-50">
          <Gamepad2 className="h-4 w-4 text-forge-400" />
          NOW PLAYING — {session.mode.toUpperCase()} vs {opponent}
        </span>
        <span className="ml-auto flex items-center gap-3 text-[11px] text-dark-400">
          <span>
            Session: <span className="font-mono text-dark-200">{sessionElapsed}</span>
          </span>
          <span className="text-dark-600">|</span>
          <span className={clsx('font-semibold', tier.textColor)}>{tier.label} Tier</span>
        </span>
      </div>

      {/* ForgeCore says */}
      <div className="border-b border-forge-500/20 bg-dark-900/60 px-5 py-4">
        <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-forge-400">
          ForgeCore Says
        </p>
        <p className="text-sm leading-relaxed text-dark-100">"{headlineRec}"</p>
      </div>

      {/* ArsenalAI alert (renders only when a trigger fires) */}
      <ArsenalAlert />

      {/* Action grid */}
      <div className="grid grid-cols-2 gap-2 px-5 py-4">
        <button
          type="button"
          onClick={() => router.push('/gameplan?tab=kill-sheet')}
          className="flex items-center justify-center gap-2 rounded-lg border border-dark-700 bg-dark-800/60 px-3 py-2.5 text-sm font-semibold text-dark-200 transition-all hover:border-forge-500/40 hover:text-forge-400"
        >
          <Target className="h-4 w-4" />
          Open Kill Sheet
        </button>
        <button
          type="button"
          onClick={() => router.push('/gameplan')}
          className="flex items-center justify-center gap-2 rounded-lg border border-dark-700 bg-dark-800/60 px-3 py-2.5 text-sm font-semibold text-dark-200 transition-all hover:border-forge-500/40 hover:text-forge-400"
        >
          <ClipboardList className="h-4 w-4" />
          Open Gameplan
        </button>
        <button
          type="button"
          onClick={onMentalReset}
          className="flex items-center justify-center gap-2 rounded-lg border border-dark-700 bg-dark-800/60 px-3 py-2.5 text-sm font-semibold text-dark-200 transition-all hover:border-forge-500/40 hover:text-forge-400"
        >
          <Brain className="h-4 w-4" />
          Quick Mental Reset
        </button>
        <button
          type="button"
          onClick={() => router.push('/vault')}
          className="flex items-center justify-center gap-2 rounded-lg border border-dark-700 bg-dark-800/60 px-3 py-2.5 text-sm font-semibold text-dark-200 transition-all hover:border-forge-500/40 hover:text-forge-400"
        >
          <StickyNote className="h-4 w-4" />
          Add Quick Note
        </button>
      </div>

      {/* In-game CTA */}
      <div className="border-t border-forge-500/20 px-5 py-4">
        {session.playing ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between rounded-lg border border-forge-500/40 bg-forge-500/15 px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-forge-400 opacity-75" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-forge-500" />
                </span>
                <span className="text-sm font-bold text-forge-300">In Game</span>
                <span className="font-mono text-sm text-dark-200">{inGameElapsed}</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleTogglePause}
                  className="inline-flex items-center gap-1 rounded-md border border-dark-700 bg-dark-800 px-2.5 py-1 text-[11px] font-medium text-dark-300 transition-colors hover:bg-dark-700"
                >
                  {session.coachingPaused ? (
                    <>
                      <Play className="h-3 w-3" /> Resume
                    </>
                  ) : (
                    <>
                      <Pause className="h-3 w-3" /> Pause Coaching
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={handleStopPlaying}
                  className="inline-flex items-center gap-1 rounded-md border border-amber-500/40 bg-amber-500/10 px-2.5 py-1 text-[11px] font-bold text-amber-300 transition-colors hover:bg-amber-500/20"
                >
                  <CheckCircle2 className="h-3 w-3" /> I&apos;m Done
                </button>
              </div>
            </div>
          </div>
        ) : session.steps.logged ? (
          <button
            type="button"
            onClick={onLogResult}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-forge-500 px-4 py-3 text-sm font-bold text-dark-950 shadow-lg shadow-forge-500/20 transition-all hover:bg-forge-400"
          >
            Continue Session
          </button>
        ) : (
          <button
            type="button"
            onClick={handleStartPlaying}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-forge-500 px-4 py-3 text-base font-bold text-dark-950 shadow-lg shadow-forge-500/20 transition-all hover:bg-forge-400"
          >
            <Play className="h-5 w-5 fill-current" />
            I&apos;m In Game — Start Coaching
          </button>
        )}
      </div>

      {/* Coaching status */}
      <div className="space-y-2 border-t border-forge-500/20 bg-dark-900/40 px-5 py-4">
        <p className="text-[10px] font-bold uppercase tracking-wider text-dark-400">
          Coaching Status
        </p>
        <CoachingStatusRow status={coaching.voice} />
        <CoachingStatusRow status={coaching.forgeCore} />
        <CoachingStatusRow status={coaching.tiltGuard} />
      </div>
    </div>
  );
}

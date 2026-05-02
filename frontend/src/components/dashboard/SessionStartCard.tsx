/**
 * Prominent "Start Session" card — the primary entry point for players
 * landing on the dashboard. Hidden when a session is already active.
 */

'use client';

import { useRouter } from 'next/navigation';
import { Play, Target, ClipboardList, BookOpen } from 'lucide-react';
import { clsx } from 'clsx';
import { useSessionStore } from '@/lib/sessionStore';

interface SessionStartCardProps {
  onLogMatch: () => void;
}

export function SessionStartCard({ onLogMatch }: SessionStartCardProps) {
  const router = useRouter();
  const session = useSessionStore((s) => s.session);
  const startSession = useSessionStore((s) => s.startSession);

  if (session) return null;

  const handleStartRanked = () => {
    startSession('ranked');
  };

  const handleStartDrill = () => {
    startSession('training');
    router.push('/drills');
  };

  const handleOpenGameplan = () => {
    router.push('/gameplan');
  };

  return (
    <div
      className={clsx(
        'relative overflow-hidden rounded-xl border border-dark-700/50 bg-dark-900 p-5 shadow-lg',
        'before:absolute before:inset-y-0 before:left-0 before:w-1 before:bg-forge-400'
      )}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-forge-500/15">
          <Play className="h-5 w-5 fill-forge-400 text-forge-400" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-bold text-dark-50">Ready to compete?</h3>
          <p className="mt-0.5 text-xs text-dark-400">
            Start a session to begin tracking and coaching.
          </p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
        <button
          type="button"
          onClick={handleStartRanked}
          className="group flex items-center justify-center gap-2 rounded-lg bg-forge-500 px-4 py-3 text-sm font-bold text-dark-950 shadow-lg shadow-forge-500/20 transition-all hover:bg-forge-400 hover:shadow-forge-500/30"
        >
          <Play className="h-4 w-4 fill-current" />
          Start Ranked Session
        </button>

        <button
          type="button"
          onClick={handleStartDrill}
          className="group flex items-center justify-center gap-2 rounded-lg border border-dark-700 bg-dark-800/60 px-4 py-3 text-sm font-semibold text-dark-200 transition-all hover:border-forge-500/40 hover:text-forge-400 hover:shadow-md hover:shadow-forge-500/10"
        >
          <Target className="h-4 w-4" />
          Start Drill
        </button>

        <button
          type="button"
          onClick={onLogMatch}
          className="group flex items-center justify-center gap-2 rounded-lg border border-dark-700 bg-dark-800/60 px-4 py-3 text-sm font-semibold text-dark-200 transition-all hover:border-forge-500/40 hover:text-forge-400 hover:shadow-md hover:shadow-forge-500/10"
        >
          <ClipboardList className="h-4 w-4" />
          Log a Match Result
        </button>

        <button
          type="button"
          onClick={handleOpenGameplan}
          className="group flex items-center justify-center gap-2 rounded-lg border border-dark-700 bg-dark-800/60 px-4 py-3 text-sm font-semibold text-dark-200 transition-all hover:border-forge-500/40 hover:text-forge-400 hover:shadow-md hover:shadow-forge-500/10"
        >
          <BookOpen className="h-4 w-4" />
          Open Gameplan
        </button>
      </div>
    </div>
  );
}

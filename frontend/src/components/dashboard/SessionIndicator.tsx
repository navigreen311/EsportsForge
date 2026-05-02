/**
 * Active session indicator widget — when a session is running, shows a live
 * timer + mode + Drill/Log Match/End Session controls. When idle, just shows
 * "No active session" (the prominent SessionStartCard is the real entry point).
 */

'use client';

import { useEffect } from 'react';
import { Gamepad2, Target, ClipboardList, Square } from 'lucide-react';
import { clsx } from 'clsx';
import Link from 'next/link';
import { Card } from '@/components/shared/Card';
import { useSessionStore, useSessionElapsed } from '@/lib/sessionStore';
import type { GameMode } from '@/lib/store';

const modeLabels: Record<GameMode, string> = {
  ranked: 'RANKED',
  tournament: 'TOURNAMENT',
  training: 'TRAINING',
};

interface SessionIndicatorProps {
  onLogMatch: () => void;
  onEndSession: () => void;
}

export default function SessionIndicator({
  onLogMatch,
  onEndSession,
}: SessionIndicatorProps) {
  const session = useSessionStore((s) => s.session);
  const hydrated = useSessionStore((s) => s.hydrated);
  const hydrate = useSessionStore((s) => s.hydrate);
  const elapsed = useSessionElapsed(session);

  useEffect(() => {
    if (!hydrated) hydrate();
  }, [hydrated, hydrate]);

  if (session) {
    return (
      <Card padding="sm" className="flex items-center gap-3">
        <span className="relative flex h-2.5 w-2.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-forge-400 opacity-75" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-forge-500" />
        </span>

        <div className="min-w-0 flex-1">
          <p className="text-xs font-bold text-forge-400">
            {modeLabels[session.mode]} — {elapsed}
          </p>
          {session.opponent && (
            <p className="truncate text-[10px] text-dark-400">vs {session.opponent}</p>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <Link
            href="/drills"
            className="rounded-md bg-dark-800 px-2 py-1 text-[10px] font-medium text-dark-300 transition-colors hover:bg-dark-700 hover:text-dark-100"
          >
            <Target className="mr-1 inline h-3 w-3" />
            Drill
          </Link>
          <button
            type="button"
            onClick={onLogMatch}
            className="rounded-md bg-dark-800 px-2 py-1 text-[10px] font-medium text-dark-300 transition-colors hover:bg-dark-700 hover:text-dark-100"
          >
            <ClipboardList className="mr-1 inline h-3 w-3" />
            Log Match
          </button>
          <button
            type="button"
            onClick={onEndSession}
            className={clsx(
              'rounded-md border border-red-500/40 bg-red-500/10 px-2.5 py-1 text-[10px] font-bold text-red-400',
              'transition-colors hover:bg-red-500/20'
            )}
          >
            <Square className="mr-1 inline h-2.5 w-2.5" />
            End Session
          </button>
        </div>
      </Card>
    );
  }

  return (
    <Card padding="sm">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-dark-800">
          <Gamepad2 className="h-4 w-4 text-dark-500" />
        </div>
        <p className="text-xs font-medium text-dark-400">No active session</p>
      </div>
    </Card>
  );
}

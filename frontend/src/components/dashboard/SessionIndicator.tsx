/**
 * Active session indicator widget — shows current session or "No active session"
 * with action buttons.
 */

'use client';

import { Radio, Gamepad2, Target, BookOpen, Square, Clock } from 'lucide-react';
import { clsx } from 'clsx';
import Link from 'next/link';
import { Card } from '@/components/shared/Card';
import type { SessionStatus } from '@/types/dashboard';

const modeLabels: Record<string, string> = {
  ranked: 'Ranked Match',
  tournament: 'Tournament Match',
  training: 'Training Session',
};

interface SessionIndicatorProps {
  session: SessionStatus | null;
}

export default function SessionIndicator({ session }: SessionIndicatorProps) {
  const isActive = session?.isActive ?? false;

  if (isActive && session) {
    return (
      <Card padding="sm" className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-forge-500/20">
          <Radio className="h-4 w-4 animate-pulse text-forge-400" />
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-xs font-bold text-forge-400">
            {modeLabels[session.type ?? ''] ?? 'Active Session'}
          </p>
          <p className="truncate text-[10px] text-dark-400">
            {session.opponent ? `vs ${session.opponent}` : 'In progress'}
            {session.score ? ` — ${session.score}` : ''}
            {session.startedAt && (
              <span className="ml-1 inline-flex items-center gap-0.5">
                <Clock className="inline h-2.5 w-2.5" />
                {session.startedAt}
              </span>
            )}
          </p>
        </div>

        <button className="rounded-lg border border-red-500/30 bg-red-500/10 px-2.5 py-1 text-[10px] font-bold text-red-400 transition-colors hover:bg-red-500/20">
          <Square className="mr-1 inline h-2.5 w-2.5" />
          End Session
        </button>

        <span className="relative flex h-2.5 w-2.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-forge-400 opacity-75" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-forge-500" />
        </span>
      </Card>
    );
  }

  return (
    <Card padding="sm">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-dark-800">
          <Gamepad2 className="h-4 w-4 text-dark-500" />
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium text-dark-400">No active session</p>
        </div>

        <div className="flex items-center gap-1.5">
          <Link
            href="/drills"
            className="rounded-md bg-dark-800 px-2 py-1 text-[10px] font-medium text-dark-300 transition-colors hover:bg-dark-700 hover:text-dark-100"
          >
            <Target className="mr-1 inline h-3 w-3" />
            Drill
          </Link>
          <Link
            href="/analytics"
            className="rounded-md bg-dark-800 px-2 py-1 text-[10px] font-medium text-dark-300 transition-colors hover:bg-dark-700 hover:text-dark-100"
          >
            <Gamepad2 className="mr-1 inline h-3 w-3" />
            Log Match
          </Link>
          <Link
            href="/gameplan"
            className="rounded-md bg-dark-800 px-2 py-1 text-[10px] font-medium text-dark-300 transition-colors hover:bg-dark-700 hover:text-dark-100"
          >
            <BookOpen className="mr-1 inline h-3 w-3" />
            Gameplan
          </Link>
        </div>
      </div>
    </Card>
  );
}

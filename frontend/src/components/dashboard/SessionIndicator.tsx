/**
 * Active session indicator widget — shows current session or "No active session".
 */

'use client';

import { Radio, Gamepad2 } from 'lucide-react';
import { clsx } from 'clsx';
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

  return (
    <Card padding="sm" className="flex items-center gap-3">
      <div
        className={clsx(
          'flex h-8 w-8 items-center justify-center rounded-full',
          isActive ? 'bg-forge-500/20' : 'bg-dark-800'
        )}
      >
        {isActive ? (
          <Radio className="h-4 w-4 animate-pulse text-forge-400" />
        ) : (
          <Gamepad2 className="h-4 w-4 text-dark-500" />
        )}
      </div>

      <div className="min-w-0 flex-1">
        {isActive && session ? (
          <>
            <p className="text-xs font-bold text-forge-400">
              {modeLabels[session.type ?? ''] ?? 'Active Session'}
            </p>
            <p className="truncate text-[10px] text-dark-400">
              {session.opponent
                ? `vs ${session.opponent}`
                : 'In progress'}
              {session.score ? ` — ${session.score}` : ''}
            </p>
          </>
        ) : (
          <>
            <p className="text-xs font-medium text-dark-400">
              No active session
            </p>
            <p className="text-[10px] text-dark-500">
              Start a drill or match to begin
            </p>
          </>
        )}
      </div>

      {isActive && (
        <span className="relative flex h-2.5 w-2.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-forge-400 opacity-75" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-forge-500" />
        </span>
      )}
    </Card>
  );
}

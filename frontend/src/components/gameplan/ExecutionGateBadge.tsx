/**
 * PlayerTwin Execution Gate Badge — shows execution readiness status on a play card.
 */

"use client";

import { clsx } from 'clsx';
import { AlertTriangle } from 'lucide-react';

export type ExecutionStatus =
  | 'competition-ready'
  | 'practicing'
  | 'learning'
  | 'not-mastered';

interface ExecutionGateBadgeProps {
  status: ExecutionStatus;
}

const statusConfig: Record<
  ExecutionStatus,
  { label: string; style: string; icon?: boolean }
> = {
  'competition-ready': {
    label: 'Competition Ready',
    style: 'bg-forge-500/20 text-forge-400 border-forge-500/30',
  },
  practicing: {
    label: 'Practicing',
    style: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  },
  learning: {
    label: 'Learning',
    style: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  },
  'not-mastered': {
    label: 'Not Mastered',
    style: 'bg-red-500/20 text-red-400 border-red-500/30',
    icon: true,
  },
};

export function ExecutionGateBadge({ status }: ExecutionGateBadgeProps) {
  const { label, style, icon } = statusConfig[status];

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium',
        style,
        status !== 'competition-ready' && 'opacity-80'
      )}
    >
      {icon && <AlertTriangle className="h-3 w-3" />}
      {label}
    </span>
  );
}

/** Mock mapping of play IDs to their execution readiness status. */
export const PLAY_EXECUTION_STATUS: Record<string, ExecutionStatus> = {
  'play-1': 'competition-ready',
  'play-2': 'competition-ready',
  'play-3': 'practicing',
  'play-4': 'learning',
  'play-5': 'competition-ready',
  'play-6': 'not-mastered',
  'play-7': 'practicing',
  'play-8': 'competition-ready',
  'play-9': 'learning',
  'play-10': 'not-mastered',
};

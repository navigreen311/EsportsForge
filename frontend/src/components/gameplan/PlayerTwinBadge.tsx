/**
 * PlayerTwin Execution Badge — Per-play "Execution: XX%" badge.
 * Green >75%, Yellow 50-75%, Red <50%.
 */

'use client';

import { clsx } from 'clsx';

interface PlayerTwinBadgeProps {
  executionPct: number;
}

function getBadgeStyle(pct: number) {
  if (pct > 75) return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
  if (pct >= 50) return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
  return 'bg-red-500/20 text-red-400 border-red-500/30';
}

export default function PlayerTwinBadge({ executionPct }: PlayerTwinBadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-bold tabular-nums',
        getBadgeStyle(executionPct)
      )}
    >
      Execution: {executionPct}%
    </span>
  );
}

/** Mock execution percentages per play ID */
export const PLAY_EXECUTION_PCT: Record<string, number> = {
  'play-1': 88,
  'play-2': 72,
  'play-3': 78,
  'play-4': 45,
  'play-5': 81,
  'play-6': 38,
  'play-7': 65,
  'play-8': 92,
  'play-9': 55,
  'play-10': 42,
};

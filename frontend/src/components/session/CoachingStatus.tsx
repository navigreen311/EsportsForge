/**
 * Compact "● Subsystem: Status — detail" rows for the competition card.
 */

'use client';

import { clsx } from 'clsx';
import type { DotTone, SubsystemStatus } from '@/hooks/useCoachingStatus';

const TONE: Record<DotTone, { dot: string; label: string }> = {
  green: { dot: 'bg-forge-400', label: 'text-forge-300' },
  amber: { dot: 'bg-amber-400', label: 'text-amber-300' },
  red: { dot: 'bg-red-400', label: 'text-red-300' },
};

export function CoachingStatusRow({ status }: { status: SubsystemStatus }) {
  const tone = TONE[status.tone];
  return (
    <div className="flex items-start gap-2 text-xs">
      <span className="mt-1.5 flex h-2 w-2 flex-shrink-0">
        <span
          className={clsx(
            'absolute inline-flex h-2 w-2 rounded-full opacity-60',
            status.tone === 'green' && 'animate-ping',
            tone.dot
          )}
        />
        <span className={clsx('relative inline-flex h-2 w-2 rounded-full', tone.dot)} />
      </span>
      <div className="min-w-0 flex-1">
        <span className={clsx('font-semibold', tone.label)}>{status.label}</span>
        <span className="text-dark-400"> — {status.detail}</span>
      </div>
    </div>
  );
}

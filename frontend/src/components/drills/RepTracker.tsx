/**
 * Per-rep dot row. Each dot encodes one of four states:
 *   ✓ green  = success (manual or auto-detected)
 *   ✗ red    = fail
 *   ● amber  = currently watching (in-progress)
 *   ○ gray   = upcoming
 */

'use client';

import { Check, Loader2, X } from 'lucide-react';
import { clsx } from 'clsx';

export type RepStatus = 'success' | 'fail' | 'in-progress' | 'pending';

export interface RepDot {
  index: number;
  status: RepStatus;
  autoDetected?: boolean;
}

interface RepTrackerProps {
  totalReps: number;
  reps: RepDot[];
}

export default function RepTracker({ totalReps, reps }: RepTrackerProps) {
  const byIndex = new Map(reps.map((r) => [r.index, r]));

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {Array.from({ length: totalReps }, (_, i) => {
        const dot = byIndex.get(i + 1) ?? { index: i + 1, status: 'pending' as const };

        const base =
          'flex h-7 w-7 items-center justify-center rounded-full border text-[10px] font-bold tabular-nums';
        if (dot.status === 'success') {
          return (
            <div
              key={dot.index}
              className={clsx(base, 'border-forge-500/40 bg-forge-500/15 text-forge-300')}
              title={`Rep ${dot.index} — success${dot.autoDetected ? ' (auto)' : ''}`}
            >
              <Check className="h-3.5 w-3.5" />
            </div>
          );
        }
        if (dot.status === 'fail') {
          return (
            <div
              key={dot.index}
              className={clsx(base, 'border-red-500/40 bg-red-500/15 text-red-300')}
              title={`Rep ${dot.index} — fail${dot.autoDetected ? ' (auto)' : ''}`}
            >
              <X className="h-3.5 w-3.5" />
            </div>
          );
        }
        if (dot.status === 'in-progress') {
          return (
            <div
              key={dot.index}
              className={clsx(base, 'border-amber-400/50 bg-amber-500/10 text-amber-300')}
              title={`Rep ${dot.index} — in progress`}
            >
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            </div>
          );
        }
        return (
          <div
            key={dot.index}
            className={clsx(base, 'border-dark-700 bg-dark-800/50 text-dark-500')}
            title={`Rep ${dot.index} — pending`}
          >
            {dot.index}
          </div>
        );
      })}
    </div>
  );
}

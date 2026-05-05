/**
 * Compact "render in progress" state for AnimaPlayer.
 *
 * Shows a spinner, the AnimaForge brand line, and a simple time-remaining
 * estimate driven by `estimatedSeconds` (or a sensible default). Reusable
 * outside AnimaPlayer if any agent wants to surface render progress in
 * a different layout.
 */

'use client';

import { useEffect, useState } from 'react';
import { Film, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';

export interface AnimaPendingStateProps {
  /** Estimated render time in seconds — drives the countdown. */
  estimatedSeconds?: number;
  /** 0–100 progress reported by AnimaForge, when available. */
  progress?: number;
  /** Optional override of the headline copy. */
  label?: string;
  /** Compact mode for inline use (drill queue card hover, etc.). */
  compact?: boolean;
  className?: string;
}

const DEFAULT_ESTIMATE_SECONDS = 45;

export function AnimaPendingState({
  estimatedSeconds,
  progress,
  label,
  compact,
  className,
}: AnimaPendingStateProps) {
  const total = estimatedSeconds ?? DEFAULT_ESTIMATE_SECONDS;
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    setElapsed(0);
    const id = setInterval(() => {
      setElapsed((e) => e + 1);
    }, 1000);
    return () => clearInterval(id);
  }, [total]);

  const remaining = Math.max(0, total - elapsed);
  // Prefer the server-reported progress when present; fall back to the
  // local clock so the bar still moves while the first poll round-trips.
  const pct = typeof progress === 'number'
    ? Math.min(100, Math.max(0, progress))
    : Math.min(95, Math.round((elapsed / total) * 100));

  if (compact) {
    return (
      <div
        className={clsx(
          'flex items-center gap-2 rounded-md border border-dark-700 bg-dark-800/60 px-2.5 py-1.5 text-[11px] text-dark-300',
          className,
        )}
        role="status"
        aria-live="polite"
      >
        <Loader2 className="h-3 w-3 animate-spin text-forge-400" />
        <span>Generating animation…</span>
        <span className="text-dark-500">~{remaining}s</span>
      </div>
    );
  }

  return (
    <div
      className={clsx(
        'rounded-lg border border-forge-500/30 bg-dark-900/80 p-4',
        className,
      )}
      role="status"
      aria-live="polite"
    >
      <div className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-forge-300">
        <Film className="h-3.5 w-3.5" />
        {label ?? 'Generating animation…'}
        <Loader2 className="ml-auto h-3.5 w-3.5 animate-spin text-forge-400" />
      </div>

      {/* Progress bar */}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-dark-800">
        <div
          className="h-full bg-forge-500 transition-all duration-700 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="mt-2 flex items-center justify-between text-[11px] text-dark-400">
        <span>AnimaForge is rendering your clip.</span>
        <span className="font-mono text-dark-300">~{remaining}s</span>
      </div>
      <p className="mt-1 text-[10px] text-dark-500">
        We&apos;ll notify you when it&apos;s ready.
      </p>
    </div>
  );
}

export default AnimaPendingState;

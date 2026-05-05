/**
 * "Animation unavailable" state — shown when an AnimaForge render fails or
 * the polling hook has surfaced a hard error. Provides a [Try Again] button
 * that calls back into the parent so the parent can re-fetch / re-trigger.
 */

'use client';

import { AlertTriangle, RotateCcw } from 'lucide-react';
import { clsx } from 'clsx';

export interface AnimaErrorStateProps {
  /** Optional human-readable error from the backend. */
  message?: string | null;
  /** Number of retry attempts already made. */
  attempt?: number;
  /** Maximum retries before the parent should give up. */
  maxAttempts?: number;
  /** Called when the user clicks [Try Again]. */
  onRetry?: () => void;
  /** Hide the retry button (e.g. after maxAttempts is reached). */
  retryDisabled?: boolean;
  className?: string;
}

export function AnimaErrorState({
  message,
  attempt,
  maxAttempts,
  onRetry,
  retryDisabled,
  className,
}: AnimaErrorStateProps) {
  const showAttemptCount =
    typeof attempt === 'number' && typeof maxAttempts === 'number' && attempt > 0;

  return (
    <div
      className={clsx(
        'flex items-center justify-between gap-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3',
        className,
      )}
      role="alert"
    >
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-400" />
        <div>
          <p className="text-xs font-semibold text-amber-200">
            Animation unavailable
          </p>
          {message && (
            <p className="mt-0.5 text-[11px] text-amber-200/80">{message}</p>
          )}
          {showAttemptCount && (
            <p className="mt-0.5 text-[10px] text-amber-200/60">
              Attempt {attempt}/{maxAttempts}
            </p>
          )}
        </div>
      </div>

      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          disabled={retryDisabled}
          className="inline-flex items-center gap-1 rounded-md border border-amber-500/40 bg-amber-500/10 px-2.5 py-1 text-[11px] font-bold text-amber-200 hover:bg-amber-500/20 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <RotateCcw className="h-3 w-3" />
          Try Again
        </button>
      )}
    </div>
  );
}

export default AnimaErrorState;

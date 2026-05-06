/**
 * Per-page Watching status hint — small inline badge that complements the
 * global floating WatchingWidget. Shows two states:
 *
 *   - WATCHING: green "👁 Watching this page" badge so the player can see
 *     at a glance that frames are flowing for *this* surface.
 *   - OFF / RESTRICTED: muted hint reminding the player to enable Watching
 *     for live coaching (or noting the anti-cheat restriction).
 *
 * Place near the page header — caller passes `pageName` so the hint reports
 * itself into the global widget context.
 */

'use client';

import { Eye, EyeOff, Lock } from 'lucide-react';
import { clsx } from 'clsx';
import { useUIStore } from '@/lib/store';
import {
  useReportWatchingPage,
  useWatchingStore,
} from '@/lib/watchingStore';

interface Props {
  /** Human-readable page name surfaced into the global widget. */
  pageName: string;
  /** Optional copy override for the OFF state. */
  offHint?: string;
  /** Optional override for the WATCHING state. */
  onHint?: string;
  className?: string;
}

export function WatchingPageHint({
  pageName,
  offHint,
  onHint,
  className,
}: Props) {
  useReportWatchingPage(pageName);

  const isWatching = useWatchingStore((s) => s.isWatching);
  const pausedUntil = useWatchingStore((s) => s.pausedUntil);
  const currentMode = useUIStore((s) => s.currentMode);
  const isRestricted =
    currentMode === 'ranked' || currentMode === 'tournament';
  const isPaused = pausedUntil !== null && pausedUntil > Date.now();

  if (isRestricted) {
    return (
      <div
        className={clsx(
          'inline-flex items-center gap-1.5 rounded-md border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[11px] font-medium text-amber-300',
          className
        )}
        title="Watching is disabled in ranked / tournament modes (anti-cheat)."
      >
        <Lock className="h-3 w-3" />
        Watching disabled in this mode
      </div>
    );
  }

  if (isWatching) {
    return (
      <div
        className={clsx(
          'inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[11px] font-medium',
          isPaused
            ? 'border-amber-500/40 bg-amber-500/10 text-amber-300'
            : 'border-forge-500/40 bg-forge-500/10 text-forge-300',
          className
        )}
      >
        <Eye className="h-3 w-3" />
        {isPaused
          ? 'Watching paused'
          : (onHint ?? `Watching ${pageName}`)}
      </div>
    );
  }

  return (
    <div
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-md border border-dark-700 bg-dark-900/60 px-2.5 py-1 text-[11px] font-medium text-dark-400',
        className
      )}
      title="Click the eye icon in the top bar to start watching."
    >
      <EyeOff className="h-3 w-3" />
      {offHint ?? 'Enable Watching for live coaching'}
    </div>
  );
}

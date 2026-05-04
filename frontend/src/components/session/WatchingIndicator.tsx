/**
 * Watching indicator — shown wherever VisionAudioForge is actively monitoring
 * the player's screen. Same component is mounted in ranked sessions, drill
 * lab, SimLab, and Arsenal Practice.
 */

'use client';

import { Eye, X } from 'lucide-react';
import { clsx } from 'clsx';

export type WatchingMode = 'ranked' | 'drill' | 'simlab' | 'arsenal';

const MODE_LABEL: Record<WatchingMode, string> = {
  ranked: 'Watching your ranked game',
  drill: 'Watching your drill execution',
  simlab: 'Watching SimLab scenario execution',
  arsenal: 'Watching secret weapon practice',
};

interface Props {
  isWatching: boolean;
  onStop: () => void;
  mode: WatchingMode;
  /** Optional per-instance suffix, e.g. weapon name or scenario name. */
  detail?: string;
  className?: string;
}

export function WatchingIndicator({
  isWatching,
  onStop,
  mode,
  detail,
  className,
}: Props) {
  if (!isWatching) return null;

  return (
    <div
      className={clsx(
        'flex items-center gap-3 rounded-lg border border-forge-500/40 bg-forge-500/10 px-4 py-2.5',
        className
      )}
    >
      <span className="relative flex h-2.5 w-2.5">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-forge-400 opacity-75" />
        <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-forge-400" />
      </span>
      <Eye className="h-4 w-4 text-forge-300" />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-bold text-forge-200">
          VisionAudioForge Watching · LIVE
        </p>
        <p className="truncate text-[11px] text-forge-300/80">
          {MODE_LABEL[mode]}
          {detail ? ` — ${detail}` : ''}
        </p>
      </div>
      <button
        type="button"
        onClick={onStop}
        className="inline-flex items-center gap-1 rounded-md border border-red-500/40 bg-red-500/10 px-2 py-1 text-[11px] font-bold text-red-300 hover:bg-red-500/20"
      >
        <X className="h-3 w-3" />
        Stop
      </button>
    </div>
  );
}

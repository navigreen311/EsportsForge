/**
 * Floating Watching widget — a global, persistent surface that shows up at
 * bottom-right whenever VisionAudioForge is monitoring. It mirrors the
 * canonical state from `useWatchingStore` so it works on every page without
 * each page mounting its own indicator.
 *
 * Mounted once in `(dashboard)/layout.tsx` between the FeedbackButton (left)
 * and the ShareWinModalHost (full-screen overlay).
 */

'use client';

import { useEffect, useState } from 'react';
import { Eye, Pause, Play, Square, ChevronDown, Settings } from 'lucide-react';
import Link from 'next/link';
import { clsx } from 'clsx';
import {
  CAPTURE_SOURCE_LABEL,
  useBootstrapWatchingStore,
  useWatchingStore,
} from '@/lib/watchingStore';

function formatPauseRemaining(ms: number): string {
  const total = Math.max(0, Math.ceil(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  if (m === 0) return `${s}s`;
  return `${m}m ${String(s).padStart(2, '0')}s`;
}

export default function WatchingWidget() {
  // Bootstrap the persisted captureSource on first mount so the eye-icon
  // toggle can short-circuit the modal when the player has already chosen.
  useBootstrapWatchingStore();

  const isWatching = useWatchingStore((s) => s.isWatching);
  const pausedUntil = useWatchingStore((s) => s.pausedUntil);
  const captureSource = useWatchingStore((s) => s.captureSource);
  const lastPageContext = useWatchingStore((s) => s.lastPageContext);
  const lastDetectionLabel = useWatchingStore((s) => s.lastDetectionLabel);
  const stop = useWatchingStore((s) => s.stop);
  const pauseFor = useWatchingStore((s) => s.pauseFor);
  const unpause = useWatchingStore((s) => s.unpause);

  const [collapsed, setCollapsed] = useState(false);
  // Re-tick once a second while paused so the countdown ticks down.
  const [, setTick] = useState(0);
  useEffect(() => {
    if (!pausedUntil) return;
    const id = window.setInterval(() => setTick((t) => t + 1), 1000);
    return () => window.clearInterval(id);
  }, [pausedUntil]);

  if (!isWatching) return null;

  const isPaused = pausedUntil !== null && pausedUntil > Date.now();
  const remainingMs = isPaused ? Math.max(0, (pausedUntil ?? 0) - Date.now()) : 0;

  if (collapsed) {
    return (
      <button
        type="button"
        onClick={() => setCollapsed(false)}
        title={isPaused ? 'Watching paused — click to expand' : 'Watching live — click to expand'}
        className={clsx(
          'fixed bottom-4 right-4 z-40 flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-bold shadow-lg backdrop-blur-sm transition-colors',
          isPaused
            ? 'border-amber-500/50 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20'
            : 'border-forge-500/50 bg-forge-500/10 text-forge-300 hover:bg-forge-500/20'
        )}
      >
        <span className="relative flex h-2 w-2">
          {!isPaused && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-forge-400 opacity-75" />
          )}
          <span
            className={clsx(
              'relative inline-flex h-2 w-2 rounded-full',
              isPaused ? 'bg-amber-400' : 'bg-forge-400'
            )}
          />
        </span>
        <Eye className="h-3.5 w-3.5" />
        {isPaused ? `Paused ${formatPauseRemaining(remainingMs)}` : 'Watching'}
      </button>
    );
  }

  return (
    <div
      className={clsx(
        'fixed bottom-4 right-4 z-40 w-72 rounded-xl border bg-dark-900/95 shadow-xl backdrop-blur-sm',
        isPaused ? 'border-amber-500/40' : 'border-forge-500/40'
      )}
    >
      <div className="flex items-center gap-2 border-b border-dark-700/60 px-4 py-2">
        <span className="relative flex h-2.5 w-2.5">
          {!isPaused && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-forge-400 opacity-75" />
          )}
          <span
            className={clsx(
              'relative inline-flex h-2.5 w-2.5 rounded-full',
              isPaused ? 'bg-amber-400' : 'bg-forge-400'
            )}
          />
        </span>
        <Eye className={clsx('h-4 w-4', isPaused ? 'text-amber-300' : 'text-forge-300')} />
        <p className={clsx('flex-1 text-xs font-bold', isPaused ? 'text-amber-200' : 'text-forge-200')}>
          {isPaused ? `Paused — ${formatPauseRemaining(remainingMs)}` : 'Watching · LIVE'}
        </p>
        <button
          type="button"
          onClick={() => setCollapsed(true)}
          className="rounded-md p-1 text-dark-400 transition-colors hover:bg-dark-800 hover:text-dark-200"
          aria-label="Collapse"
        >
          <ChevronDown className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="space-y-1 px-4 py-3 text-[11px]">
        <p className="text-dark-300">
          <span className="text-dark-500">Source: </span>
          <span className="font-medium text-dark-100">
            {captureSource ? CAPTURE_SOURCE_LABEL[captureSource] : 'Not configured'}
          </span>
        </p>
        {lastPageContext && (
          <p className="text-dark-300">
            <span className="text-dark-500">Page: </span>
            <span className="font-medium text-dark-100">{lastPageContext}</span>
          </p>
        )}
        {lastDetectionLabel && (
          <p className="text-dark-300">
            <span className="text-dark-500">Last detected: </span>
            <span className="font-medium text-dark-100">{lastDetectionLabel}</span>
          </p>
        )}
        {!lastDetectionLabel && !isPaused && (
          <p className="italic text-dark-500">
            Standing by for in-game frames…
          </p>
        )}
      </div>

      <div className="flex items-center gap-1.5 border-t border-dark-700/60 px-3 py-2">
        {isPaused ? (
          <button
            type="button"
            onClick={unpause}
            className="inline-flex items-center gap-1 rounded-md border border-forge-500/40 bg-forge-500/10 px-2 py-1 text-[11px] font-medium text-forge-300 transition-colors hover:bg-forge-500/20"
          >
            <Play className="h-3 w-3" />
            Resume
          </button>
        ) : (
          <button
            type="button"
            onClick={() => pauseFor(5)}
            title="Pause monitoring for 5 minutes"
            className="inline-flex items-center gap-1 rounded-md border border-dark-700 bg-dark-800 px-2 py-1 text-[11px] font-medium text-dark-300 transition-colors hover:bg-dark-700"
          >
            <Pause className="h-3 w-3" />
            Pause 5m
          </button>
        )}
        <button
          type="button"
          onClick={stop}
          className="inline-flex items-center gap-1 rounded-md border border-red-500/40 bg-red-500/10 px-2 py-1 text-[11px] font-bold text-red-300 transition-colors hover:bg-red-500/20"
        >
          <Square className="h-3 w-3" />
          Stop
        </button>
        <Link
          href="/settings?tab=game"
          title="Open Watching settings"
          className="ml-auto inline-flex items-center gap-1 rounded-md border border-dark-700 bg-dark-800 px-2 py-1 text-[11px] font-medium text-dark-300 transition-colors hover:bg-dark-700"
        >
          <Settings className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}

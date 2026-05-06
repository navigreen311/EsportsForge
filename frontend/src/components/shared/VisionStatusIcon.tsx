'use client';

import { useState } from 'react';
import { Eye, EyeOff, Lock } from 'lucide-react';
import { clsx } from 'clsx';
import { useUIStore } from '@/lib/store';
import { useWatchingStore } from '@/lib/watchingStore';
import { VisionAudioForgeService } from '@/lib/services/visionaudioforge';
import { CaptureSourceModal } from '@/components/session/CaptureSourceModal';

/**
 * Canonical Watching toggle in the top bar.
 *
 * UX:
 *   - OFF + capture source not configured → opens CaptureSourceModal; on
 *     selection, transitions to ON.
 *   - OFF + source configured            → toggles to ON immediately.
 *   - ON                                  → toggles to OFF.
 *   - Restricted (ranked / tournament mode) → button is disabled with a Lock
 *     overlay and a tooltip explaining the anti-cheat policy. Clicks no-op.
 *   - Paused                              → amber dot + "paused" tooltip; click
 *     still toggles to OFF (player can stop a paused session).
 */
export default function VisionStatusIcon() {
  const currentMode = useUIStore((s) => s.currentMode);
  const isWatching = useWatchingStore((s) => s.isWatching);
  const pausedUntil = useWatchingStore((s) => s.pausedUntil);
  const captureSource = useWatchingStore((s) => s.captureSource);
  const start = useWatchingStore((s) => s.start);
  const stop = useWatchingStore((s) => s.stop);
  const setSource = useWatchingStore((s) => s.setSource);
  const [showCaptureModal, setShowCaptureModal] = useState(false);

  const isRestricted =
    currentMode === 'ranked' || currentMode === 'tournament';
  const isPaused = pausedUntil !== null && pausedUntil > Date.now();

  const tooltip = isRestricted
    ? 'Watching is disabled in ranked / tournament modes (anti-cheat).'
    : isWatching
      ? isPaused
        ? 'Paused — click to stop'
        : 'Watching live — click to stop'
      : captureSource
        ? 'Click to start watching'
        : 'Click to set up watching';

  const handleClick = () => {
    if (isRestricted) return;
    if (isWatching) {
      stop();
      return;
    }
    if (!captureSource) {
      setShowCaptureModal(true);
      return;
    }
    start();
  };

  return (
    <>
      <button
        onClick={handleClick}
        disabled={isRestricted}
        className={clsx(
          'relative rounded-lg p-2 transition-colors',
          isRestricted
            ? 'cursor-not-allowed text-amber-400 opacity-70'
            : isWatching
              ? 'text-forge-300 hover:bg-forge-500/10'
              : 'text-dark-400 hover:bg-dark-800 hover:text-dark-200'
        )}
        title={tooltip}
        aria-label={tooltip}
        aria-pressed={isWatching}
      >
        {isRestricted ? (
          <span className="relative inline-flex">
            <Eye className="h-5 w-5" />
            <Lock className="absolute -bottom-0.5 -right-0.5 h-3 w-3 text-amber-400" />
          </span>
        ) : isWatching ? (
          <Eye className="h-5 w-5" />
        ) : (
          <EyeOff className="h-5 w-5" />
        )}

        {/* Status dot — green pulsing when live, amber when paused. */}
        {isWatching && !isPaused && (
          <span className="absolute right-1 top-1 inline-flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-forge-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-forge-400" />
          </span>
        )}
        {isWatching && isPaused && (
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-amber-400" />
        )}
      </button>

      <CaptureSourceModal
        open={showCaptureModal}
        onClose={() => setShowCaptureModal(false)}
        onSelected={(source) => {
          // CaptureSourceModal already wrote to localStorage via
          // VisionAudioForgeService.setCaptureSource — mirror it into the
          // store and proceed straight to ON.
          setSource(source);
          setShowCaptureModal(false);
          start();
          // Defensive: keep VisionAudioForgeService and store in lock-step
          // even if the modal's persistence path changes underneath us.
          try {
            VisionAudioForgeService.setCaptureSource(source);
          } catch {
            /* noop */
          }
        }}
      />
    </>
  );
}

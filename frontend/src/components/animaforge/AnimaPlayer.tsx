/**
 * AnimaPlayer — the shared video surface for every AnimaForge integration.
 *
 * Per contract §5 it implements four states:
 *
 *   1. PENDING      — spinner + "Generating animation… ~Xs", polls every 5s.
 *   2. COMPLETE     — HTML5 <video> with poster, controls, autoplay-muted,
 *                     loop (default true for diagrams, false for share-win).
 *   3. FAILED       — "Animation unavailable — [Try Again]" button. After
 *                     `maxRetries` (3) without success, calls `onError`.
 *   4. UNAVAILABLE  — render `null` (parent should ALSO gate via
 *                     `useAnimaForgeAvailable()`).
 *
 * Either `jobId` OR `videoUrl` must be provided. If `videoUrl` is provided,
 * polling is skipped and the player renders the COMPLETE state immediately.
 */

'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { clsx } from 'clsx';
import { useAnimaForgeAvailable, useAnimaForgeJob } from '@/hooks/useAnimaForge';
import type { AnimaPlayerType } from '@/lib/animaforge/types';
import { AnimaPendingState } from './AnimaPendingState';
import { AnimaErrorState } from './AnimaErrorState';

const MAX_RETRIES = 3;

export interface AnimaPlayerProps {
  /** Job to poll. Either jobId OR videoUrl must be provided. */
  jobId?: string;
  /** Direct video URL — skips polling. */
  videoUrl?: string;
  thumbnailUrl?: string;
  type: AnimaPlayerType;
  /** Auto-play muted on mount (default: true for short diagrams). */
  autoPlay?: boolean;
  /** Loop short diagrams (default: true for diagrams, false for share-win). */
  loop?: boolean;
  /** Fired once when video is ready to play. Receives the resolved videoUrl. */
  onReady?: (videoUrl: string) => void;
  /** Fired when render fails permanently (after max retries). */
  onError?: (message: string) => void;
  /** Override polling interval ms — default 5000 */
  pollIntervalMs?: number;
  /** Optional extra class on the outer wrapper. */
  className?: string;
}

export function AnimaPlayer({
  jobId,
  videoUrl,
  thumbnailUrl,
  type,
  autoPlay,
  loop,
  onReady,
  onError,
  pollIntervalMs,
  className,
}: AnimaPlayerProps) {
  // -------------------------------------------------------------------------
  // Availability gate — silent when AnimaForge is offline (contract §1).
  // -------------------------------------------------------------------------
  const { available, loading: availabilityLoading } = useAnimaForgeAvailable();

  // -------------------------------------------------------------------------
  // Job polling. Disabled when we already have a direct videoUrl.
  // -------------------------------------------------------------------------
  const pollEnabled = !videoUrl && !!jobId && available !== false;
  const { job, error: jobError, refresh } = useAnimaForgeJob(jobId, {
    pollIntervalMs,
    enabled: pollEnabled,
  });

  const [retries, setRetries] = useState(0);
  const [hardError, setHardError] = useState<string | null>(null);
  const onReadyFiredRef = useRef(false);
  const onErrorFiredRef = useRef(false);

  // -------------------------------------------------------------------------
  // Derived state — pick one of the four UI states.
  // -------------------------------------------------------------------------
  const resolvedVideoUrl = videoUrl ?? job?.video_url ?? null;
  const resolvedThumbnail = thumbnailUrl ?? job?.thumbnail_url ?? undefined;

  const state: 'unavailable' | 'pending' | 'complete' | 'failed' = useMemo(() => {
    if (available === false) return 'unavailable';
    if (hardError) return 'failed';
    if (resolvedVideoUrl) return 'complete';
    if (job?.status === 'failed') return 'failed';
    if (job?.status === 'complete' && !resolvedVideoUrl) {
      // status complete but no URL is effectively a failure
      return 'failed';
    }
    if (jobId || availabilityLoading) return 'pending';
    return 'pending';
  }, [available, hardError, resolvedVideoUrl, job, jobId, availabilityLoading]);

  // -------------------------------------------------------------------------
  // Fire onReady once when we land in COMPLETE.
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (state === 'complete' && resolvedVideoUrl && !onReadyFiredRef.current) {
      onReadyFiredRef.current = true;
      onReady?.(resolvedVideoUrl);
    }
  }, [state, resolvedVideoUrl, onReady]);

  // -------------------------------------------------------------------------
  // Retry handling. Each click bumps the counter and re-fetches the job.
  // After MAX_RETRIES with the job still failed, we fire onError once.
  // -------------------------------------------------------------------------
  const handleRetry = useCallback(() => {
    setRetries((r) => r + 1);
    setHardError(null);
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (state !== 'failed') return;
    if (retries >= MAX_RETRIES && !onErrorFiredRef.current) {
      onErrorFiredRef.current = true;
      const msg =
        job?.error_message ||
        hardError ||
        jobError?.message ||
        'Animation render failed';
      onError?.(msg);
    }
  }, [state, retries, job?.error_message, hardError, jobError, onError]);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  // UNAVAILABLE — fully silent.
  if (state === 'unavailable') return null;

  // Sanity check: must have either jobId or videoUrl.
  if (!jobId && !videoUrl) {
    // Don't crash — silently render nothing. Parent should gate.
    return null;
  }

  const effectiveAutoPlay = autoPlay ?? true;
  const effectiveLoop = loop ?? type !== 'share-win';

  return (
    <div
      className={clsx('w-full', className)}
      data-animaforge-state={state}
      data-animaforge-type={type}
    >
      {state === 'pending' && (
        <AnimaPendingState
          estimatedSeconds={job?.estimated_seconds}
          progress={job?.progress}
        />
      )}

      {state === 'complete' && resolvedVideoUrl && (
        <div className="overflow-hidden rounded-lg border border-dark-700 bg-black">
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <video
            key={resolvedVideoUrl}
            src={resolvedVideoUrl}
            poster={resolvedThumbnail}
            controls
            autoPlay={effectiveAutoPlay}
            muted={effectiveAutoPlay}
            loop={effectiveLoop}
            playsInline
            preload="metadata"
            className="block h-auto w-full"
          />
        </div>
      )}

      {state === 'failed' && (
        <AnimaErrorState
          message={
            job?.error_message ?? hardError ?? jobError?.message ?? undefined
          }
          attempt={retries}
          maxAttempts={MAX_RETRIES}
          onRetry={handleRetry}
          retryDisabled={retries >= MAX_RETRIES}
        />
      )}
    </div>
  );
}

export default AnimaPlayer;

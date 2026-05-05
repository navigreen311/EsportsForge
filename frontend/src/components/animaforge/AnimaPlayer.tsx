/**
 * AnimaPlayer — STUB.
 *
 * Agent #8 placed this so PlayDetail compiles. Agent #3 owns the real
 * implementation (pending spinner / HTML5 video / failed-state retry).
 */

'use client';

import type { AnimaPlayerType } from '@/lib/animaforge/types';

export type { AnimaPlayerType };

export interface AnimaPlayerProps {
  jobId?: string;
  videoUrl?: string;
  thumbnailUrl?: string;
  type: AnimaPlayerType;
  autoPlay?: boolean;
  loop?: boolean;
  onReady?: (videoUrl: string) => void;
  onError?: (message: string) => void;
  pollIntervalMs?: number;
}

export default function AnimaPlayer({
  jobId,
  videoUrl,
  thumbnailUrl,
  type,
  autoPlay = true,
  loop = true,
}: AnimaPlayerProps) {
  if (videoUrl) {
    return (
      <video
        src={videoUrl}
        poster={thumbnailUrl}
        autoPlay={autoPlay}
        muted
        loop={loop}
        controls
        className="w-full rounded-lg border border-dark-700 bg-black"
      />
    );
  }
  return (
    <div className="flex items-center justify-center rounded-lg border border-dark-700 bg-dark-900 p-6 text-sm text-dark-400">
      Generating animation… {jobId ? `(${type})` : ''}
    </div>
  );
}

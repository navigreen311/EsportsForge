/**
 * AnimaPlayer — shared video player for AnimaForge renders.
 *
 * NOTE: This file is owned by Agent #3 per the AnimaForge contract. The
 * version below is a STUB created on the share-win branch (Agent #9) so
 * dependent files type-check in isolation. Agent #3's branch will replace
 * this with the canonical implementation (polling, pending-state, retries)
 * at merge time.
 */

"use client";

import { useEffect } from "react";
import type { AnimaPlayerProps } from "@/lib/animaforge/types";

export function AnimaPlayer({
  jobId,
  videoUrl,
  thumbnailUrl,
  type: _type,
  autoPlay = true,
  loop = true,
  onReady,
}: AnimaPlayerProps) {
  useEffect(() => {
    if (videoUrl && onReady) onReady(videoUrl);
  }, [videoUrl, onReady]);

  if (!videoUrl) {
    return (
      <div className="flex h-48 w-full items-center justify-center bg-dark-950 text-sm text-dark-400">
        Generating animation… {jobId ? `(${jobId.slice(0, 8)}…)` : ""}
      </div>
    );
  }

  return (
    <video
      src={videoUrl}
      poster={thumbnailUrl}
      autoPlay={autoPlay}
      loop={loop}
      muted
      controls
      className="h-auto w-full"
    />
  );
}

export default AnimaPlayer;

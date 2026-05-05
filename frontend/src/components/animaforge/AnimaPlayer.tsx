/**
 * AnimaPlayer — STUB FILE.
 *
 * Temporary type-check stub created by Agent #7 (drill-frontend) so the
 * drill component edits compile in this worktree. Agent #3 owns the
 * canonical AnimaPlayer at this same path; at merge time their version
 * replaces this stub. Props surface mirrors §5 of the contract.
 */

"use client";

import { useEffect } from "react";
import type { AnimaPlayerType } from "@/lib/animaforge/types";

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

  if (videoUrl) {
    return (
      <video
        src={videoUrl}
        poster={thumbnailUrl}
        autoPlay={autoPlay}
        muted
        loop={loop}
        controls
        playsInline
        className="w-full rounded-lg bg-black"
      />
    );
  }

  if (jobId) {
    return (
      <div className="rounded-lg border border-dark-700 bg-dark-800/40 p-4 text-sm text-dark-300">
        Generating animation… we will notify you when it is ready.
      </div>
    );
  }

  return null;
}

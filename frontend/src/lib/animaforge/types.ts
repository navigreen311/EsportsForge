/**
 * AnimaForge — shared TypeScript types.
 *
 * NOTE: This file is owned by Agent #3 per the AnimaForge contract. The
 * version below is a STUB created on the share-win branch (Agent #9) so
 * dependent files type-check in isolation. Agent #3's branch will replace
 * this with the canonical implementation at merge time.
 */

export type AnimaPlayerType =
  | "weapon-diagram"
  | "drill-demo"
  | "play-diagram"
  | "share-win";

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

export interface AnimaForgeJob {
  job_id: string;
  type: AnimaPlayerType;
  status: "pending" | "rendering" | "complete" | "failed";
  video_url?: string | null;
  thumbnail_url?: string | null;
  progress?: number;
  completed_at?: string | null;
}

// STUB — Agent #3's version replaces at merge.
// Mirrors the prop interface from contract §5 so consumers compile.
'use client';

export type AnimaPlayerType =
  | 'weapon-diagram'
  | 'drill-demo'
  | 'play-diagram'
  | 'share-win';

export interface AnimaPlayerProps {
  /** Job to poll. Either jobId OR videoUrl must be provided. */
  jobId?: string;
  /** Direct video URL — skips polling. */
  videoUrl?: string;
  thumbnailUrl?: string;
  type: AnimaPlayerType;
  /** Auto-play muted on mount (default: true for short diagrams) */
  autoPlay?: boolean;
  /** Loop short diagrams (default: true for diagrams, false for share-win) */
  loop?: boolean;
  /** Fired once when video is ready to play. Receives the resolved videoUrl. */
  onReady?: (videoUrl: string) => void;
  /** Fired when render fails permanently (after max retries). */
  onError?: (message: string) => void;
  /** Override polling interval ms — default 5000 */
  pollIntervalMs?: number;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function AnimaPlayer(_props: AnimaPlayerProps) {
  return null;
}

export default AnimaPlayer;

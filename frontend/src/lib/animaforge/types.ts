/**
 * Shared TypeScript types for AnimaForge consumers.
 *
 * STUB placed by Agent #8 so other agents' files type-check before Agent #3
 * lands. Agent #3 owns this file on merge.
 */

export type AnimaPlayerType =
  | 'weapon-diagram'
  | 'drill-demo'
  | 'play-diagram'
  | 'share-win';

export type AnimaJobStatus = 'pending' | 'rendering' | 'complete' | 'failed';

export interface AnimaForgeJob {
  jobId: string;
  type: AnimaPlayerType;
  status: AnimaJobStatus;
  videoUrl?: string;
  thumbnailUrl?: string;
  progress?: number;
  completedAt?: string;
}

export interface AnimaForgeStatus {
  available: boolean;
}

export interface PlayDiagramRenderResult {
  jobId?: string;
  estimatedSeconds?: number;
  status?: AnimaJobStatus;
  videoUrl?: string;
  thumbnailUrl?: string;
  cached?: boolean;
}

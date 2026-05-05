// STUB — Agent #3's version replaces at merge.
// Provides the hook signatures other agents import against.
'use client';

export interface AnimaForgeAvailability {
  available: boolean | null;
  isLoading: boolean;
}

export function useAnimaForgeAvailable(): AnimaForgeAvailability {
  // STUB: returns null (unknown) so consumers do not show animation UI on
  // their own branches. Agent #3's real hook performs an SWR query against
  // GET /api/v1/animaforge/status.
  return { available: null, isLoading: false };
}

export interface AnimaForgeJobShape {
  job_id: string;
  status: 'pending' | 'rendering' | 'complete' | 'failed';
  video_url?: string;
  thumbnail_url?: string;
  progress?: number;
}

export function useAnimaForgeJob(_jobId: string | null | undefined): {
  job: AnimaForgeJobShape | null;
  isLoading: boolean;
} {
  return { job: null, isLoading: false };
}

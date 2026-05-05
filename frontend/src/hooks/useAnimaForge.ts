/**
 * AnimaForge availability + job-status hooks.
 *
 * STUB placed by Agent #8 so other agents' files compile before Agent #3
 * lands. Agent #3 owns this file on merge and will likely back it with SWR.
 */

'use client';

import { useEffect, useState } from 'react';

import api from '@/lib/api';
import type { AnimaForgeJob } from '@/lib/animaforge/types';

/**
 * Returns true when AnimaForge is online. Defaults to false so UI hides
 * silently when the service is unconfigured.
 */
export function useAnimaForgeAvailable(): boolean {
  const [available, setAvailable] = useState(false);
  useEffect(() => {
    let cancelled = false;
    api
      .get<{ available: boolean }>('/animaforge/status')
      .then((r) => {
        if (!cancelled) setAvailable(Boolean(r.data?.available));
      })
      .catch(() => {
        if (!cancelled) setAvailable(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);
  return available;
}

export function useAnimaForgeJob(jobId: string | undefined): AnimaForgeJob | null {
  // Stub: real implementation polls /api/v1/animaforge/jobs/{job_id} every 5s.
  // Returning null is fine for type-checking; the AnimaPlayer component owns
  // its own polling internally.
  void jobId;
  return null;
}

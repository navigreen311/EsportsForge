/**
 * useAnimaForge — availability + job-polling hooks for AnimaForge.
 *
 * NOTE: This file is owned by Agent #3 per the AnimaForge contract. The
 * version below is a STUB created on the share-win branch (Agent #9) so
 * dependent files type-check in isolation. Agent #3's branch will replace
 * this with the canonical SWR-backed implementation at merge time.
 */

"use client";

import { useEffect, useState } from "react";
import type { AnimaForgeJob } from "@/lib/animaforge/types";

/**
 * Stub: returns true once the AnimaForge status endpoint reports `available`,
 * false otherwise. Fails closed (false) on network error so the UI hides
 * silently per the graceful-degradation rule.
 */
export function useAnimaForgeAvailable(): boolean {
  const [available, setAvailable] = useState<boolean>(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const apiModule = await import("@/lib/api");
        const api = apiModule.default;
        const res = await api.get<{ available: boolean }>("/animaforge/status");
        if (!cancelled) setAvailable(Boolean(res.data?.available));
      } catch {
        if (!cancelled) setAvailable(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return available;
}

/** Stub: caller-supplied jobId polls /api/v1/animaforge/jobs/{jobId}. */
export function useAnimaForgeJob(jobId?: string): AnimaForgeJob | null {
  const [job, setJob] = useState<AnimaForgeJob | null>(null);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;
    (async () => {
      try {
        const apiModule = await import("@/lib/api");
        const api = apiModule.default;
        const res = await api.get<AnimaForgeJob>(`/animaforge/jobs/${jobId}`);
        if (!cancelled) setJob(res.data);
      } catch {
        if (!cancelled) setJob(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  return job;
}

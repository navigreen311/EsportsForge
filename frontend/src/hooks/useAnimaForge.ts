/**
 * useAnimaForge — STUB FILE.
 *
 * Temporary type-check stub created by Agent #7 (drill-frontend). Agent #3
 * owns the canonical implementation (with SWR-cached availability + job
 * polling). At merge time their version replaces this stub. Consumers in
 * Agents 5/7/8/9/10 import from this path and treat it as a black box.
 */

"use client";

import { useEffect, useState } from "react";
import { animaforgeApi } from "@/lib/animaforge/api";
import type { AnimaForgeJob } from "@/lib/animaforge/types";

export interface UseAnimaForgeAvailableResult {
  /** undefined while loading; true/false once resolved. */
  available: boolean | undefined;
  isLoading: boolean;
}

/**
 * Returns AnimaForge availability. Cached at module scope so multiple
 * mounts share the same probe. Returns `undefined` on first render so
 * consumers can show "loading" silently and avoid a flash of UI.
 */
let cachedAvailable: boolean | undefined;
let probePromise: Promise<boolean> | null = null;

export function useAnimaForgeAvailable(): UseAnimaForgeAvailableResult {
  const [available, setAvailable] = useState<boolean | undefined>(
    cachedAvailable,
  );
  const [isLoading, setIsLoading] = useState<boolean>(
    cachedAvailable === undefined,
  );

  useEffect(() => {
    if (cachedAvailable !== undefined) {
      setAvailable(cachedAvailable);
      setIsLoading(false);
      return;
    }
    let cancelled = false;
    if (!probePromise) {
      probePromise = animaforgeApi
        .getStatus()
        .then((r) => {
          cachedAvailable = !!r.available;
          return cachedAvailable;
        })
        .catch(() => {
          cachedAvailable = false;
          return false;
        });
    }
    probePromise.then((v) => {
      if (cancelled) return;
      setAvailable(v);
      setIsLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return { available, isLoading };
}

export interface UseAnimaForgeJobResult {
  job: AnimaForgeJob | null;
  isLoading: boolean;
  error: string | null;
}

/** Stub — Agent #3 implements polling. Returns null/loading by default. */
export function useAnimaForgeJob(_jobId?: string | null): UseAnimaForgeJobResult {
  return { job: null, isLoading: false, error: null };
}

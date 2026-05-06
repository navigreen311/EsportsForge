/**
 * AnimaForge React hooks.
 *
 *   - `useAnimaForgeAvailable()`  — caches `/animaforge/status` for 60s in
 *     module scope so every gated component shares one network call.
 *   - `useAnimaForgeJob(jobId)`   — polls `/animaforge/jobs/{id}` every 5s
 *     while the job is still pending/rendering, then stops.
 *
 * Plain `useState` + `useEffect` (no SWR / React Query). The contract
 * (§5) explicitly allows either; staying dep-free keeps the surface small
 * and the polling lifecycle obvious.
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { getAvailability, getJob } from '@/lib/animaforge/api';
import type { AnimaForgeJob } from '@/lib/animaforge/types';

// ---------------------------------------------------------------------------
// useAnimaForgeAvailable — module-level 60s cache
// ---------------------------------------------------------------------------

const AVAILABILITY_TTL_MS = 60_000;

interface AvailabilityCache {
  value: boolean | null;
  fetchedAt: number;
  inflight: Promise<boolean> | null;
}

const availabilityCache: AvailabilityCache = {
  value: null,
  fetchedAt: 0,
  inflight: null,
};

/**
 * Subscribers are notified whenever the cache flips so multiple hook
 * instances stay in sync with a single fetch.
 */
const subscribers = new Set<(value: boolean | null) => void>();

function publishAvailability(value: boolean | null) {
  availabilityCache.value = value;
  availabilityCache.fetchedAt = Date.now();
  subscribers.forEach((fn) => fn(value));
}

async function refreshAvailability(): Promise<boolean> {
  if (availabilityCache.inflight) return availabilityCache.inflight;
  const p = (async () => {
    try {
      const res = await getAvailability();
      const value = !!res?.available;
      publishAvailability(value);
      return value;
    } catch {
      publishAvailability(false);
      return false;
    } finally {
      availabilityCache.inflight = null;
    }
  })();
  availabilityCache.inflight = p;
  return p;
}

export interface UseAnimaForgeAvailableResult {
  /** `null` while the first request is pending, then `true`/`false`. */
  available: boolean | null;
  loading: boolean;
}

/**
 * Returns whether AnimaForge is reachable. Cached for 60s across all
 * components — the underlying `/animaforge/status` is only called once per
 * minute regardless of how many components subscribe.
 */
export function useAnimaForgeAvailable(): UseAnimaForgeAvailableResult {
  const [available, setAvailable] = useState<boolean | null>(availabilityCache.value);
  const [loading, setLoading] = useState<boolean>(availabilityCache.value === null);

  useEffect(() => {
    let cancelled = false;
    const sub = (v: boolean | null) => {
      if (!cancelled) {
        setAvailable(v);
        setLoading(false);
      }
    };
    subscribers.add(sub);

    const fresh =
      availabilityCache.value !== null &&
      Date.now() - availabilityCache.fetchedAt < AVAILABILITY_TTL_MS;

    if (fresh) {
      setAvailable(availabilityCache.value);
      setLoading(false);
    } else {
      setLoading(true);
      refreshAvailability().catch(() => {
        // Already handled inside refreshAvailability — swallow here so the
        // useEffect promise chain doesn't surface unhandled-rejection logs.
      });
    }

    return () => {
      cancelled = true;
      subscribers.delete(sub);
    };
  }, []);

  return { available, loading };
}

// ---------------------------------------------------------------------------
// useAnimaForgeJob — polling job watcher
// ---------------------------------------------------------------------------

const DEFAULT_POLL_INTERVAL_MS = 5000;

export interface UseAnimaForgeJobOptions {
  /** Override polling cadence in ms. Default 5000. */
  pollIntervalMs?: number;
  /** When `false`, the hook stays idle and never fetches. Default `true`. */
  enabled?: boolean;
}

export interface UseAnimaForgeJobResult {
  job: AnimaForgeJob | null;
  loading: boolean;
  error: Error | null;
  /** Manually re-fetch the job (e.g. after a retry click). */
  refresh: () => Promise<void>;
}

/**
 * Polls `/animaforge/jobs/{jobId}` every `pollIntervalMs` until the job is
 * `complete` or `failed`. Pass `enabled={false}` (or omit `jobId`) to keep
 * the hook idle.
 */
export function useAnimaForgeJob(
  jobId?: string,
  options?: UseAnimaForgeJobOptions,
): UseAnimaForgeJobResult {
  const { pollIntervalMs = DEFAULT_POLL_INTERVAL_MS, enabled = true } = options ?? {};

  const [job, setJob] = useState<AnimaForgeJob | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const cancelledRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchOnce = useCallback(async () => {
    if (!jobId) return;
    setLoading(true);
    try {
      const next = await getJob(jobId);
      if (cancelledRef.current) return;
      setJob(next);
      setError(null);
    } catch (e) {
      if (cancelledRef.current) return;
      setError(e instanceof Error ? e : new Error('Failed to fetch job'));
    } finally {
      if (!cancelledRef.current) setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    cancelledRef.current = false;

    if (!jobId || !enabled) {
      // Reset job so consumers don't see stale data when disabled / cleared.
      if (!jobId) setJob(null);
      return () => {
        cancelledRef.current = true;
        if (timerRef.current) {
          clearTimeout(timerRef.current);
          timerRef.current = null;
        }
      };
    }

    // Recursive poll — schedule the next tick only after the previous fetch
    // resolves, and only while the status is still in-flight.
    const tick = async () => {
      if (cancelledRef.current) return;
      try {
        const next = await getJob(jobId);
        if (cancelledRef.current) return;
        setJob(next);
        setError(null);
        const terminal = next.status === 'complete' || next.status === 'failed';
        if (!terminal) {
          timerRef.current = setTimeout(tick, pollIntervalMs);
        }
      } catch (e) {
        if (cancelledRef.current) return;
        setError(e instanceof Error ? e : new Error('Failed to fetch job'));
        // On transient errors, keep trying — the backend or network may recover.
        timerRef.current = setTimeout(tick, pollIntervalMs);
      } finally {
        if (!cancelledRef.current) setLoading(false);
      }
    };

    setLoading(true);
    void tick();

    return () => {
      cancelledRef.current = true;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [jobId, enabled, pollIntervalMs]);

  return { job, loading, error, refresh: fetchOnce };
}

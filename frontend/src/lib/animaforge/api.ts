/**
 * Typed HTTP client wrappers around `/api/v1/animaforge/*`.
 *
 * Uses the shared axios instance from `@/lib/api` (which handles base URL,
 * NextAuth JWT injection, and 401-redirect). Every call here goes through
 * the FastAPI backend — the frontend never talks to AnimaForge directly
 * (per contract §1).
 *
 * Other agents (5/7/8/9/10) import from this module; they must NOT redefine
 * these shapes elsewhere.
 */

import api from '@/lib/api';
import type {
  AnimaForgeAvailability,
  AnimaForgeJob,
  AnimaForgeRenderResponse,
} from './types';

// ---------------------------------------------------------------------------
// Core endpoints (Agent #1 owns; surfaces are stable per contract §4)
// ---------------------------------------------------------------------------

/**
 * GET `/animaforge/status` — used by `useAnimaForgeAvailable()` to gate UI.
 * Returns `{ available: false }` on any error so the UI hides silently
 * (graceful-degradation per contract §1).
 */
export async function getAvailability(): Promise<AnimaForgeAvailability> {
  try {
    const res = await api.get<AnimaForgeAvailability>('/animaforge/status');
    return res.data ?? { available: false };
  } catch {
    return { available: false };
  }
}

/**
 * GET `/animaforge/jobs/{job_id}` — fetch a single render job. Used by
 * `useAnimaForgeJob()` for polling and by the My-Animations library.
 */
export async function getJob(jobId: string): Promise<AnimaForgeJob> {
  const res = await api.get<AnimaForgeJob>(`/animaforge/jobs/${encodeURIComponent(jobId)}`);
  return res.data;
}

/**
 * GET `/animaforge/jobs` — list the authenticated user's jobs (My
 * Animations library page). Returns at most ~50 most-recent.
 */
export async function listJobs(): Promise<AnimaForgeJob[]> {
  const res = await api.get<AnimaForgeJob[] | { items: AnimaForgeJob[] }>('/animaforge/jobs');
  // Tolerate either a bare list or an envelope `{items: [...]}` so we don't
  // break if Agent #1 picks a paginated shape.
  if (Array.isArray(res.data)) return res.data;
  if (res.data && Array.isArray((res.data as { items?: AnimaForgeJob[] }).items)) {
    return (res.data as { items: AnimaForgeJob[] }).items;
  }
  return [];
}

/**
 * DELETE `/animaforge/jobs/{job_id}` — soft-delete the user's job. Used by
 * the library page's [Delete] action.
 */
export async function deleteJob(jobId: string): Promise<void> {
  await api.delete(`/animaforge/jobs/${encodeURIComponent(jobId)}`);
}

// ---------------------------------------------------------------------------
// Feature-render helpers — convenience POSTs for the four render kinds.
// Each returns the discriminated `AnimaForgeRenderResponse` so callers can
// distinguish a cached hit from a queued job.
// ---------------------------------------------------------------------------

/** Convenience: POST `/animaforge/arsenal` (weapon diagrams). */
export async function requestArsenalRender(payload: {
  weapon_id: string;
}): Promise<AnimaForgeRenderResponse> {
  const res = await api.post<AnimaForgeRenderResponse>('/animaforge/arsenal', payload);
  return res.data;
}

/** Convenience: POST `/animaforge/drill` (drill demos — shared, system-owned). */
export async function requestDrillRender(payload: {
  title_id: string;
  drill_type: string;
  drill_name?: string;
}): Promise<AnimaForgeRenderResponse> {
  const res = await api.post<AnimaForgeRenderResponse>('/animaforge/drill', payload);
  return res.data;
}

/** Convenience: POST `/animaforge/play` (gameplan play diagrams). */
export async function requestPlayRender(payload: {
  play_id: string;
  title_id?: string;
  coverage?: string;
  opponent_coverage?: string;
}): Promise<AnimaForgeRenderResponse> {
  const res = await api.post<AnimaForgeRenderResponse>('/animaforge/play', payload);
  return res.data;
}

/** Convenience: POST `/animaforge/share-win` (achievement cards). */
export async function requestShareWinRender(payload: {
  trigger_type: string;
  trigger_data: Record<string, unknown>;
}): Promise<AnimaForgeRenderResponse> {
  const res = await api.post<AnimaForgeRenderResponse>('/animaforge/share-win', payload);
  return res.data;
}

// ---------------------------------------------------------------------------
// Cached-status lookups (used by feature panels on mount, e.g.
// WeaponDetail's `useEffect` pre-fetch).
// ---------------------------------------------------------------------------

/**
 * GET `/animaforge/arsenal/status?weapon_id=...` — returns the cached job
 * for a weapon if one exists, otherwise `null`. Owned by Agent #4.
 */
export async function getArsenalStatus(
  weaponId: string,
): Promise<Partial<AnimaForgeJob>> {
  try {
    const res = await api.get<AnimaForgeJob | null>('/animaforge/arsenal/status', {
      params: { weapon_id: weaponId },
    });
    return res.data ?? {};
  } catch {
    return {};
  }
}

/**
 * GET `/animaforge/drill/status?title_id=...&drill_type=...` — cached drill
 * demo lookup. Owned by Agent #6.
 */
export async function getDrillStatus(params: {
  title_id: string;
  drill_type: string;
}): Promise<Partial<AnimaForgeJob>> {
  try {
    const res = await api.get<AnimaForgeJob | null>('/animaforge/drill/status', { params });
    return res.data ?? {};
  } catch {
    return {};
  }
}

/**
 * GET `/animaforge/play/status?play_id=...&coverage=...` — cached play
 * diagram lookup. Owned by Agent #8.
 */
export async function getPlayStatus(params: {
  play_id: string;
  coverage?: string;
  opponent_coverage?: string;
}): Promise<Partial<AnimaForgeJob>> {
  try {
    const res = await api.get<AnimaForgeJob | null>('/animaforge/play/status', { params });
    return res.data ?? {};
  } catch {
    return {};
  }
}

// ---------------------------------------------------------------------------
// Aliases consumed by feature components (added during merge — keep stable).
// ---------------------------------------------------------------------------

/**
 * Alias for `getPlayStatus` — used by gameplan components which call it as
 * `getPlayDiagramStatus(playId, coverage)` (positional). Accepts both shapes.
 */
export async function getPlayDiagramStatus(
  playIdOrParams: string | { play_id: string; coverage?: string; opponent_coverage?: string },
  coverage?: string,
): Promise<Partial<AnimaForgeJob>> {
  const params =
    typeof playIdOrParams === 'string'
      ? { play_id: playIdOrParams, coverage }
      : playIdOrParams;
  return getPlayStatus(params);
}

/** Alias for `requestPlayRender` — used by gameplan components. */
export const renderPlayDiagram = requestPlayRender;

/**
 * Namespace export — feature components prefer `animaforgeApi.getJob(...)`
 * over individual named imports. Just re-bundles the named exports above.
 */
export const animaforgeApi = {
  getAvailability,
  getJob,
  listJobs,
  deleteJob,
  requestArsenalRender,
  requestDrillRender,
  requestPlayRender,
  requestShareWinRender,
  getArsenalStatus,
  getDrillStatus,
  getPlayStatus,
  getPlayDiagramStatus,
  renderPlayDiagram,
};

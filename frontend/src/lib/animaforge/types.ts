/**
 * Shared TypeScript types for the AnimaForge integration.
 *
 * Mirrors the backend contract documented in
 * `docs/integrations/animaforge_contract.md` (sections 2 & 4). Every
 * frontend module that talks to `/api/v1/animaforge/*` should import
 * from this file rather than redefining shapes.
 */

// ---------------------------------------------------------------------------
// Job kinds & status
// ---------------------------------------------------------------------------

/** The four animation kinds AnimaForge can render for EsportsForge. */
export type AnimaPlayerType =
  | 'weapon-diagram'
  | 'drill-demo'
  | 'play-diagram'
  | 'share-win';

/** Lifecycle of an AnimaForge render job. */
export type AnimaJobStatus = 'pending' | 'rendering' | 'complete' | 'failed';

// ---------------------------------------------------------------------------
// Job model — wire shape returned by GET /api/v1/animaforge/jobs/{job_id}
// ---------------------------------------------------------------------------

/**
 * The canonical job-row shape the FastAPI backend returns. Optional fields
 * mirror the contract (§4 response shape):
 *   - `video_url` / `thumbnail_url` are populated only once status === "complete"
 *   - `progress` is 0–100, present while rendering
 *   - `completed_at` is ISO-8601, set on completion or failure
 *   - `error_message` is populated on failure
 *   - `estimated_seconds` is included on the initial POST response
 */
export interface AnimaForgeJob {
  job_id: string;
  type: AnimaPlayerType;
  status: AnimaJobStatus;
  source_id?: string;
  title_id?: string;
  video_url?: string | null;
  thumbnail_url?: string | null;
  progress?: number;
  estimated_seconds?: number;
  error_message?: string | null;
  completed_at?: string | null;
  created_at?: string;
  // Compatibility aliases — feature components written with the blueprint's
  // camelCase prop names. These echo the snake_case fields above so callers
  // can use whichever convention they prefer.
  videoUrl?: string | null;
  thumbnailUrl?: string | null;
  jobId?: string;
}

// ---------------------------------------------------------------------------
// Render-request response (POST /api/v1/animaforge/<feature>)
// ---------------------------------------------------------------------------

/**
 * Cached-result response — the requested animation already exists, so the
 * backend skips queueing a new render and returns the URLs directly.
 */
export interface AnimaForgeCachedResult {
  video_url?: string | null;
  videoUrl?: string | null;
  thumbnail_url?: string | null;
  thumbnailUrl?: string | null;
  cached?: boolean;
  job_id?: string | null;
  jobId?: string | null;
}

/**
 * Pending-job response — a fresh render was queued. Frontend should poll
 * `/jobs/{job_id}` (or rely on the webhook-driven notification) until the
 * status flips to `complete` or `failed`.
 */
export interface AnimaForgePendingJob {
  job_id?: string | null;
  jobId?: string | null;
  estimated_seconds?: number;
  status?: 'pending' | 'rendering' | 'complete' | 'failed';
  cached?: boolean;
  video_url?: string | null;
  videoUrl?: string | null;
  thumbnail_url?: string | null;
  thumbnailUrl?: string | null;
}

/**
 * Permissive union — wire shape varies between cache-hit and pending-job. We
 * accept either field-naming convention so feature components written before
 * the snake_case standardization still type-check.
 */
export type AnimaForgeRenderResponse = AnimaForgeCachedResult | AnimaForgePendingJob;

/** Alias for play-diagram render results — consumed by gameplan components. */
export type PlayDiagramRenderResult = AnimaForgeRenderResponse;

// ---------------------------------------------------------------------------
// Status / availability
// ---------------------------------------------------------------------------

export interface AnimaForgeAvailability {
  available: boolean;
}

// ---------------------------------------------------------------------------
// Share-Win triggers (placeholder — Agent #9 owns the canonical shape)
// ---------------------------------------------------------------------------

/**
 * The trigger-event kinds that produce a "share your win" animated card.
 * Agent #9 may extend this; keep it widened (`string` fallback) so other
 * modules don't break on unknown kinds.
 */
// `(string & {})` keeps autocomplete on the literal union while still
// accepting forward-compat strings from agents that extend the trigger set.
// This is a deliberate idiom — silence the ban-types warning on the line
// that uses it.
export type ShareWinTriggerType =
  | 'tournament-win'
  | 'benchmark-milestone'
  | 'win-streak'
  | 'impactrank-fix'
  | 'playertwin-accuracy'
  // eslint-disable-next-line @typescript-eslint/ban-types
  | (string & {});

/**
 * Minimal placeholder shape for a pending share-win trigger. Agent #9 will
 * own the authoritative version inside `share_triggers.py` / their own
 * frontend module — this exists only so other agents can reference the type
 * before that lands. Keep `data` loosely typed.
 */
export interface ShareWinTrigger {
  type: ShareWinTriggerType;
  /** Free-form payload — title-id, percentile, streak count, etc. */
  data: Record<string, unknown>;
  /** Job_id once the render has been queued (optional). */
  job_id?: string;
  /** ISO-8601 timestamp of when the trigger was created. */
  created_at?: string;
}

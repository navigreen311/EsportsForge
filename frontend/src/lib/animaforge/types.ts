/**
 * AnimaForge shared types — STUB FILE.
 *
 * This is a temporary type-check stub created by Agent #7 (drill-frontend)
 * so the worktree's `tsc --noEmit` passes in isolation. Agent #3 owns the
 * canonical implementation at this same path; at merge time, Agent #3's
 * version replaces this stub.
 *
 * Surface mirrors §5 of `docs/integrations/animaforge_contract.md`.
 */

export type AnimaPlayerType =
  | "weapon-diagram"
  | "drill-demo"
  | "play-diagram"
  | "share-win";

export type AnimaForgeJobStatus =
  | "pending"
  | "rendering"
  | "complete"
  | "failed";

export interface AnimaForgeJob {
  job_id: string;
  type: AnimaPlayerType;
  status: AnimaForgeJobStatus;
  video_url?: string | null;
  thumbnail_url?: string | null;
  progress?: number;
  completed_at?: string | null;
}

export interface AnimaForgeStatusResponse {
  available: boolean;
}

/** Response of POST /animaforge/<feature> endpoints (cached or pending). */
export interface AnimaForgeRenderResponse {
  /** Set when cached. */
  video_url?: string;
  thumbnail_url?: string;
  cached?: boolean;
  /** Set when pending. */
  job_id?: string;
  estimated_seconds?: number;
  status?: AnimaForgeJobStatus;
}

/** Response of GET /animaforge/drill/status?title_id=&drill_type= */
export type AnimaForgeDrillStatusResponse = AnimaForgeRenderResponse;

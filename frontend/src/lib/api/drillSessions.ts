/**
 * Thin wrapper around the FastAPI drill-session endpoints.
 *
 * Auth + base URL come from the shared axios client (`@/lib/api`), which
 * attaches the NextAuth JWT and reads NEXT_PUBLIC_API_URL.
 */

import api from "@/lib/api";

export interface DrillRepRecord {
  rep_number: number;
  success: boolean;
  auto_detected: boolean;
  confidence: number | null;
  reason: string | null;
}

export interface DrillSessionDTO {
  id: string;
  drill_id: string;
  drill_type: string | null;
  title_id: string;
  total_reps: number;
  completed_reps: number;
  success_reps: number;
  fail_reps: number;
  success_rate: number;
  auto_detected: boolean;
  status: "active" | "complete" | "abandoned";
  started_at: string;
  completed_at: string | null;
  reps: DrillRepRecord[];
}

export interface DrillRepUpdate {
  completed_reps: number;
  success_reps: number;
  fail_reps: number;
  success_rate: number;
}

export interface DrillDebriefDTO {
  success_rate: number;
  success_reps: number;
  fail_reps: number;
  total_reps: number;
  auto_detected_pct: number;
  skill_update: string;
  player_twin_note: string;
  loop_ai_insight: string;
  mastery_change: number;
  difficulty_recommendation: "increase" | "hold" | "decrease";
  next_drill_hint: string | null;
}

export interface DrillSessionCompleteDTO {
  session: DrillSessionDTO;
  debrief: DrillDebriefDTO;
}

export async function startDrillSession(args: {
  drillId: string;
  drillType?: string;
  titleId: string;
  totalReps: number;
}): Promise<DrillSessionDTO> {
  const { data } = await api.post<DrillSessionDTO>("/drill-sessions/start", {
    drill_id: args.drillId,
    drill_type: args.drillType,
    title_id: args.titleId,
    total_reps: args.totalReps,
  });
  return data;
}

export async function recordDrillRep(args: {
  sessionId: string;
  repNumber: number;
  success: boolean;
  autoDetected?: boolean;
  confidence?: number;
  reason?: string;
}): Promise<DrillRepUpdate> {
  const { data } = await api.post<DrillRepUpdate>(
    `/drill-sessions/${args.sessionId}/rep`,
    {
      rep_number: args.repNumber,
      success: args.success,
      auto_detected: args.autoDetected ?? false,
      confidence: args.confidence ?? null,
      reason: args.reason ?? null,
    },
  );
  return data;
}

export async function completeDrillSession(
  sessionId: string,
): Promise<DrillSessionCompleteDTO> {
  const { data } = await api.post<DrillSessionCompleteDTO>(
    `/drill-sessions/${sessionId}/complete`,
  );
  return data;
}

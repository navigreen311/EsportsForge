/**
 * GameplanAI client — wraps the FastAPI /gameplans + /opponents endpoints.
 */

import api from '@/lib/api';

export interface OpponentSummaryDTO {
  id: string;
  gamertag: string;
  title: string;
  archetype: string | null;
  encounter_count: number;
  has_dossier: boolean;
}

export async function listOpponents(titleId: string): Promise<OpponentSummaryDTO[]> {
  const { data } = await api.get<OpponentSummaryDTO[]>('/opponents/list', {
    params: { title: titleId },
  });
  return data;
}

export async function createOpponent(payload: {
  gamertag: string;
  title: string;
  archetype?: string | null;
}): Promise<OpponentSummaryDTO> {
  const { data } = await api.post<OpponentSummaryDTO>('/opponents', payload);
  return data;
}

export interface GenerateGameplanResponse {
  gameplan_id: string;
  gameplan: Record<string, unknown>;
  cached: boolean;
  source: 'claude' | 'mock' | 'cache';
}

export async function generateGameplan(args: {
  titleId: string;
  opponentId?: string;
  mode?: string;
  bypassCache?: boolean;
}): Promise<GenerateGameplanResponse> {
  const { data } = await api.post<GenerateGameplanResponse>(
    '/gameplans/generate',
    {
      title: args.titleId,
      opponent_id: args.opponentId,
      mode: args.mode ?? 'ranked',
      bypass_cache: args.bypassCache ?? false,
    },
  );
  return data;
}

export interface ShareLinkResponse {
  share_token: string;
  share_url_path: string;
  expires_at: string;
}

export async function shareGameplan(gameplanId: string): Promise<ShareLinkResponse> {
  const { data } = await api.post<ShareLinkResponse>(`/gameplans/${gameplanId}/share`);
  return data;
}

// ----- AdaptAI -------------------------------------------------------------

export interface AdaptResponse {
  adjustment: string;
  audible_to: string | null;
  confidence: number;
  reasoning: string;
  source: 'claude' | 'mock';
}

export async function adaptPlay(args: {
  play: Record<string, unknown>;
  opponentTendency: string;
  titleId: string;
  opponentArchetype?: string | null;
}): Promise<AdaptResponse> {
  const { data } = await api.post<AdaptResponse>('/adapt/play', {
    play: args.play,
    opponent_tendency: args.opponentTendency,
    title_id: args.titleId,
    opponent_archetype: args.opponentArchetype ?? null,
  });
  return data;
}

// ----- Scout ---------------------------------------------------------------

export interface ScoutResponse {
  opponent: OpponentSummaryDTO;
  tendencies: Record<string, unknown>;
  source: 'claude' | 'mock';
}

export async function scoutOpponent(opponentId: string): Promise<ScoutResponse> {
  const { data } = await api.post<ScoutResponse>(`/opponents/${opponentId}/scout`);
  return data;
}

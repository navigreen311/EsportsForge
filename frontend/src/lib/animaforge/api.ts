/**
 * Typed API wrappers for `/api/v1/animaforge/*`.
 *
 * STUB placed by Agent #8. Agent #3 owns this file on merge and may add
 * additional helpers (status polling, library list, etc.).
 */

import api from '@/lib/api';
import type { PlayDiagramRenderResult } from '@/lib/animaforge/types';

export interface PlayDiagramRenderRequest {
  play_id: string;
  opponent_coverage?: string | null;
}

export async function renderPlayDiagram(
  body: PlayDiagramRenderRequest
): Promise<PlayDiagramRenderResult> {
  const res = await api.post<PlayDiagramRenderResult>('/animaforge/play', body);
  return res.data;
}

export async function getPlayDiagramStatus(
  playId: string,
  opponentCoverage?: string | null
): Promise<PlayDiagramRenderResult> {
  const res = await api.get<PlayDiagramRenderResult>('/animaforge/play/status', {
    params: {
      play_id: playId,
      opponent_coverage: opponentCoverage ?? undefined,
    },
  });
  return res.data;
}

/**
 * Gameplan backend API — generate a live gameplan and map it to the frontend
 * Play shape (including animated-diagram route geometry).
 *
 * The Madden26 generate endpoint is double-prefixed on the backend
 * (`/madden26/gameplan` include prefix + the router's own `/titles/madden26`),
 * and takes a `user_id` with no auth dependency.
 */

import api from '@/lib/api';
import { mapBackendGameplan, type BackendGameplan } from '@/lib/gameplan/mapBackend';
import type { Play } from '@/types/gameplan';

const GENERATE_PATH = '/madden26/gameplan/titles/madden26/gameplan/generate';

export interface GenerateGameplanParams {
  scheme?: string;
  metaAware?: boolean;
}

/** A stable-enough client user id for the store-only endpoint. */
function userId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  // Fallback: RFC4122-ish v4 without crypto (dev only).
  return '00000000-0000-4000-8000-000000000000';
}

/**
 * Generate a gameplan from the backend and return frontend Play[]. Throws on
 * network/HTTP error so callers can fall back to mock data.
 */
export async function generateBackendGameplan(
  params: GenerateGameplanParams = {},
): Promise<Play[]> {
  const { data } = await api.post<BackendGameplan>(GENERATE_PATH, {
    user_id: userId(),
    scheme: params.scheme ?? 'west_coast',
    meta_aware: params.metaAware ?? false,
  });
  return mapBackendGameplan(data);
}

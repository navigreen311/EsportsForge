/**
 * Arsenal client hooks — wrap the /api/v1/arsenal/* endpoints with
 * @tanstack/react-query so components can subscribe declaratively.
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { useUIStore } from '@/lib/store';
import {
  TITLE_TO_ARSENAL_ID,
  type ArsenalTitleId,
} from '@/lib/arsenal/titleMeta';

// ---------------------------------------------------------------------------
// Types (mirror backend WeaponResponse)
// ---------------------------------------------------------------------------

export type WeaponSide = 'offense' | 'defense';

export interface Weapon {
  id: string;
  user_id: string | null;
  title_id: ArsenalTitleId;
  side: WeaponSide;
  name: string;
  category: string;
  sub_category: string | null;
  formation: string | null;
  play_name: string | null;
  description: string;
  instructions: string[];
  setup_steps: string[];
  when_to_use: string;
  trigger_conditions: Record<string, unknown>;
  difficulty: 'easy' | 'medium' | 'hard';
  title_specific_data: Record<string, unknown>;
  patch_version: string | null;
  source_type: 'platform' | 'user-upload' | 'web-discovery';
  source_url: string | null;
  video_url: string | null;
  thumbnail_url: string | null;
  tags: string[];
  verified: boolean;
  success_rate: number;
  times_used: number;
  community_rating: number;
  community_votes: number;
  saved: boolean;
  created_at: string;
  updated_at: string;
}

export interface WeaponFilters {
  title_id?: ArsenalTitleId;
  side?: WeaponSide;
  category?: string;
  difficulty?: 'easy' | 'medium' | 'hard';
  source?: 'platform' | 'community' | 'my-uploads';
  situation?: string;
  sort?: 'most-used' | 'highest-rated' | 'most-recent' | 'easiest';
  q?: string;
  saved_only?: boolean;
}

export interface UsageLogPayload {
  weapon_id: string;
  session_id?: string;
  title_id: ArsenalTitleId;
  game_state?: Record<string, unknown>;
  deployed?: boolean;
  worked?: boolean | null;
  outcome?: 'yes' | 'no' | 'not-used';
  opponent_adjusted?: boolean;
  notes?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function useActiveArsenalTitle(): ArsenalTitleId {
  const selected = useUIStore((s) => s.selectedTitle);
  return TITLE_TO_ARSENAL_ID[selected];
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

export function useWeapons(filters: WeaponFilters = {}) {
  const activeTitle = useActiveArsenalTitle();
  const titleId = filters.title_id ?? activeTitle;
  const params = { ...filters, title_id: titleId };

  return useQuery<Weapon[]>({
    queryKey: ['arsenal', 'weapons', params],
    queryFn: async () => {
      const { data } = await api.get<Weapon[]>('/arsenal/weapons', { params });
      return data;
    },
  });
}

export function useWeapon(id: string | null | undefined) {
  return useQuery<Weapon>({
    queryKey: ['arsenal', 'weapon', id],
    enabled: !!id,
    queryFn: async () => {
      const { data } = await api.get<Weapon>(`/arsenal/weapons/${id}`);
      return data;
    },
  });
}

export function useMyArsenal(titleId?: ArsenalTitleId) {
  const activeTitle = useActiveArsenalTitle();
  const tid = titleId ?? activeTitle;
  return useQuery<Weapon[]>({
    queryKey: ['arsenal', 'my', tid],
    queryFn: async () => {
      const { data } = await api.get<Weapon[]>('/arsenal/my-arsenal', {
        params: { title_id: tid },
      });
      return data;
    },
  });
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export function useSaveWeapon() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (weaponId: string) => {
      const { data } = await api.post<Weapon>(`/arsenal/my-arsenal/${weaponId}`);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['arsenal'] });
    },
  });
}

export function useRemoveWeapon() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (weaponId: string) => {
      await api.delete(`/arsenal/my-arsenal/${weaponId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['arsenal'] });
    },
  });
}

export function useLogUsage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: UsageLogPayload) => {
      const { data } = await api.post('/arsenal/usage-log', payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['arsenal'] });
    },
  });
}

export function useRateWeapon() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, stars }: { id: string; stars: number }) => {
      const { data } = await api.post<Weapon>(`/arsenal/weapons/${id}/rate`, {
        stars,
      });
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['arsenal'] });
    },
  });
}

export function useCreateWeapon() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<Weapon>) => {
      const { data } = await api.post<Weapon>('/arsenal/weapons', payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['arsenal'] });
    },
  });
}

export function useUpdateWeapon() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      patch,
    }: {
      id: string;
      patch: Partial<Weapon>;
    }) => {
      const { data } = await api.patch<Weapon>(`/arsenal/weapons/${id}`, patch);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['arsenal'] });
    },
  });
}

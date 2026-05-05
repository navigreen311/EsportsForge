/**
 * AnimaForge API wrappers — STUB FILE.
 *
 * Temporary type-check stub created by Agent #7 (drill-frontend). Agent #3
 * owns the canonical version at this path; their implementation replaces
 * this stub at merge time. Surface follows §4 of the contract.
 */

import api from "@/lib/api";
import type {
  AnimaForgeDrillStatusResponse,
  AnimaForgeRenderResponse,
  AnimaForgeStatusResponse,
} from "@/lib/animaforge/types";

export const animaforgeApi = {
  async getStatus(): Promise<AnimaForgeStatusResponse> {
    const res = await api.get<AnimaForgeStatusResponse>("/animaforge/status");
    return res.data;
  },

  async getDrillStatus(params: {
    title_id: string;
    drill_type: string;
  }): Promise<AnimaForgeDrillStatusResponse> {
    const res = await api.get<AnimaForgeDrillStatusResponse>(
      "/animaforge/drill/status",
      { params },
    );
    return res.data;
  },

  async requestDrillRender(body: {
    title_id: string;
    drill_type: string;
    drill_name?: string;
  }): Promise<AnimaForgeRenderResponse> {
    const res = await api.post<AnimaForgeRenderResponse>(
      "/animaforge/drill",
      body,
    );
    return res.data;
  },
};

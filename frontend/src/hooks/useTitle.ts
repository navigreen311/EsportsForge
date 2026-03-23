/**
 * Hook for selected game title state.
 * Wraps the Zustand store for title selection.
 */

"use client";

import { useUIStore, TITLE_OPTIONS } from '@/lib/store';
import type { GameTitle, TitleOption } from '@/lib/store';

export function useTitle() {
  const selectedTitle = useUIStore((s) => s.selectedTitle);
  const setTitle = useUIStore((s) => s.setTitle);

  const currentTitle: TitleOption =
    TITLE_OPTIONS.find((t) => t.id === selectedTitle) ?? TITLE_OPTIONS[0];

  const otherTitles = TITLE_OPTIONS.filter((t) => t.id !== selectedTitle);

  return {
    selectedTitle,
    currentTitle,
    otherTitles,
    titles: TITLE_OPTIONS,
    setTitle,
  };
}

export type { GameTitle, TitleOption };

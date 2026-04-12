/**
 * useActiveTitle — localStorage-backed hook for the player's active game title.
 *
 * Persists selection across page reloads. Falls back to "madden26" if
 * nothing is stored. Syncs with the Zustand UI store so sidebar and
 * dashboard stay consistent.
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import { useUIStore } from "@/lib/store";
import { getTitleData, type TitleData } from "@/data/titles";

const STORAGE_KEY = "esportsforge_active_title";
const DEFAULT_TITLE = "madden26";

function readFromStorage(): string {
  if (typeof window === "undefined") return DEFAULT_TITLE;
  try {
    return localStorage.getItem(STORAGE_KEY) ?? DEFAULT_TITLE;
  } catch {
    return DEFAULT_TITLE;
  }
}

function writeToStorage(titleId: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, titleId);
  } catch {
    // Storage full or disabled — silently ignore
  }
}

export function useActiveTitle() {
  const [activeTitleId, setActiveTitleId] = useState<string>(DEFAULT_TITLE);

  // Keep Zustand store in sync
  const setStoreTitle = useUIStore((s) => s.setTitle);

  // Hydrate from localStorage on mount
  useEffect(() => {
    const stored = readFromStorage();
    setActiveTitleId(stored);
    setStoreTitle(stored as Parameters<typeof setStoreTitle>[0]);
  }, [setStoreTitle]);

  const setActiveTitle = useCallback(
    (titleId: string) => {
      writeToStorage(titleId);
      setActiveTitleId(titleId);
      setStoreTitle(titleId as Parameters<typeof setStoreTitle>[0]);
    },
    [setStoreTitle],
  );

  const titleData: TitleData | undefined = getTitleData(activeTitleId);

  return {
    activeTitleId,
    setActiveTitle,
    titleData,
  };
}

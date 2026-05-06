/**
 * Unified watching store — single source of truth for whether
 * VisionAudioForge is actively monitoring the player's screen.
 *
 * State:
 *   - isWatching: live boolean. When true, every page that subscribes adapts
 *     its UX (badges, voice cues, status widgets, ...).
 *   - pausedUntil: epoch ms; when set + in-future, the underlying capture is
 *     suspended even though `isWatching` may still read true. The global
 *     widget exposes a 5-minute pause via this field.
 *   - captureSource: mirrors VisionAudioForgeService's localStorage value so
 *     consumers can reactively check whether a source is configured without
 *     each component remembering to re-read localStorage.
 *   - lastPageContext / lastDetectionLabel: lightweight context the floating
 *     widget displays. Per-page hints push their own page name in via
 *     `useReportWatchingPage(pageName)`.
 *
 * Persistence: nothing is persisted by default — `isWatching` should NOT
 * survive a hard refresh because that would silently re-start screen capture
 * on every page load. Capture source preference itself lives in localStorage
 * via VisionAudioForgeService and is mirrored here at boot.
 */

'use client';

import { create } from 'zustand';
import { useEffect } from 'react';
import {
  VisionAudioForgeService,
  type CaptureSource,
} from '@/lib/services/visionaudioforge';

interface WatchingState {
  isWatching: boolean;
  pausedUntil: number | null;
  captureSource: CaptureSource | null;
  /** Page name reported by the active route (e.g. "Drill Lab"). */
  lastPageContext: string | null;
  /** Last frame label surfaced by the (mock) detection loop. */
  lastDetectionLabel: string | null;

  start: () => void;
  stop: () => void;
  pauseFor: (minutes: number) => void;
  unpause: () => void;
  setSource: (source: CaptureSource | null) => void;
  reportPage: (pageName: string | null) => void;
  reportDetection: (label: string | null) => void;
}

export const useWatchingStore = create<WatchingState>((set, get) => ({
  isWatching: false,
  pausedUntil: null,
  captureSource: null,
  lastPageContext: null,
  lastDetectionLabel: null,

  start: () => {
    // Tearing pausedUntil to null on (re)start — explicit start always wins
    // over a pending pause window.
    set({ isWatching: true, pausedUntil: null });
  },

  stop: () => {
    set({
      isWatching: false,
      pausedUntil: null,
      lastDetectionLabel: null,
    });
  },

  pauseFor: (minutes: number) => {
    if (!Number.isFinite(minutes) || minutes <= 0) return;
    set({ pausedUntil: Date.now() + minutes * 60 * 1000 });
  },

  unpause: () => set({ pausedUntil: null }),

  setSource: (source) => set({ captureSource: source }),

  reportPage: (pageName) => {
    if (get().lastPageContext !== pageName) {
      set({ lastPageContext: pageName });
    }
  },

  reportDetection: (label) => set({ lastDetectionLabel: label }),
}));

// ---------------------------------------------------------------------------
// Bootstrap — read the persisted capture source out of localStorage on mount
// so the store reflects whatever VisionAudioForgeService has persisted from a
// prior session. Mounted once globally via <WatchingBootstrap /> below.
// ---------------------------------------------------------------------------

export function useBootstrapWatchingStore() {
  useEffect(() => {
    try {
      const persisted = VisionAudioForgeService.getCaptureSource();
      if (persisted) {
        useWatchingStore.getState().setSource(persisted);
      }
    } catch {
      /* localStorage unavailable — ignore */
    }
  }, []);
}

/**
 * Hook for per-page consumers — reports the page name to the store on mount
 * so the floating widget can display "Page: Drill Lab" without needing to
 * thread props through every layout. Also clears on unmount.
 */
export function useReportWatchingPage(pageName: string) {
  const reportPage = useWatchingStore((s) => s.reportPage);
  useEffect(() => {
    reportPage(pageName);
    return () => reportPage(null);
  }, [pageName, reportPage]);
}

/**
 * Convenience: derives the *effective* watching state — true only when
 * `isWatching` is on AND any active pause window has expired. Use this in
 * adapters that need to gate active monitoring; for UX-level badges that
 * should still show "Paused" copy, read `isWatching` + `pausedUntil` raw.
 */
export function useEffectiveWatching(): boolean {
  return useWatchingStore((s) => {
    if (!s.isWatching) return false;
    if (s.pausedUntil && s.pausedUntil > Date.now()) return false;
    return true;
  });
}

/** Friendly label for the configured capture source. */
export const CAPTURE_SOURCE_LABEL: Record<CaptureSource, string> = {
  'capture-card': 'TV Capture Card',
  'pc-monitor': 'PC Monitor',
  camera: 'Camera',
};

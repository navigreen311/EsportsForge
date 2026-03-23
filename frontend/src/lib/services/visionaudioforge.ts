/**
 * VisionAudioForge service wrapper with anti-cheat enforcement.
 *
 * Mock service layer implementing the VisionAudioForge interface. When the
 * dedicated VisionAudioForge microservice is available, swap the internal
 * implementation to hit the REST API while keeping the same public interface.
 *
 * Anti-cheat policy:
 *   - Screen capture and formation detection are BLOCKED in competitive modes
 *     (ranked, tournament) to prevent real-time exploitation.
 *   - Replay analysis, input telemetry, and clip export are always safe
 *     (post-game / non-competitive).
 */

import { useUIStore } from '@/lib/store';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ReplayAnalysis {
  grade: string;
  topMistake: string;
  topStrength: string;
  plays: unknown[];
  fixes: unknown[];
}

export interface ScreenCapture {
  screenshot: string;
  timestamp: number;
}

export interface FormationDetection {
  formation: string;
  confidence: number;
  blitzIndicators: boolean;
}

export interface InputTelemetry {
  stickEfficiency: number;
  overMovement: number;
  inputTiming: number;
  hesitationRate: number;
}

export interface ClipExport {
  url: string;
  format: string;
}

export interface AnalyzeReplayOptions {
  /** Restrict analysis to a specific half / quarter / period. */
  segment?: string;
}

export interface ExportClipOptions {
  /** Output format. Defaults to 'mp4'. */
  format?: string;
  /** Trim start in seconds. */
  start?: number;
  /** Trim end in seconds. */
  end?: number;
}

// ---------------------------------------------------------------------------
// Internals
// ---------------------------------------------------------------------------

const VISIONAUDIOFORGE_ENABLED =
  typeof process !== 'undefined' &&
  process.env.NEXT_PUBLIC_VISIONAUDIOFORGE_ENABLED === 'true';

/** Modes that allow real-time vision features (screen capture, detection). */
const VISION_SAFE_MODES = new Set(['offline-lab', 'training']);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Read the current integrity / game mode from the Zustand store outside of
 * a React component. Defaults to `'ranked'` (most restrictive) when the
 * store is unavailable or the value is unset.
 */
export function getIntegrityMode(): string {
  try {
    return useUIStore.getState().currentMode ?? 'ranked';
  } catch {
    // Store may not be initialised (SSR, tests, etc.).
    return 'ranked';
  }
}

/**
 * Returns `true` when the current mode permits real-time vision features.
 */
function isVisionAllowed(): boolean {
  return VISION_SAFE_MODES.has(getIntegrityMode());
}

// ---------------------------------------------------------------------------
// Service
// ---------------------------------------------------------------------------

export const VisionAudioForgeService = {
  // -----------------------------------------------------------------------
  // analyzeReplay
  // -----------------------------------------------------------------------

  /**
   * Analyse a recorded replay file. Always safe (post-game).
   *
   * When the VisionAudioForge REST service is live this will POST the file
   * to the analysis endpoint.
   */
  async analyzeReplay(
    _file: File | Blob | ArrayBuffer,
    _opts?: AnalyzeReplayOptions,
  ): Promise<ReplayAnalysis> {
    try {
      if (!VISIONAUDIOFORGE_ENABLED) {
        return {
          grade: 'B+',
          topMistake: 'Late reads on Cover 3',
          topStrength: 'Red zone execution',
          plays: [],
          fixes: [],
        };
      }

      // TODO: POST to VisionAudioForge REST API when available.
      return {
        grade: 'B+',
        topMistake: 'Late reads on Cover 3',
        topStrength: 'Red zone execution',
        plays: [],
        fixes: [],
      };
    } catch (error) {
      console.error('[VisionAudioForge] analyzeReplay failed:', error);
      return {
        grade: 'N/A',
        topMistake: 'Analysis unavailable',
        topStrength: 'Analysis unavailable',
        plays: [],
        fixes: [],
      };
    }
  },

  // -----------------------------------------------------------------------
  // captureScreen
  // -----------------------------------------------------------------------

  /**
   * Capture the current screen. **Blocked** in competitive modes to prevent
   * real-time exploitation (anti-cheat enforcement).
   */
  async captureScreen(): Promise<ScreenCapture | null> {
    try {
      if (!isVisionAllowed()) {
        console.warn(
          `[VisionAudioForge] captureScreen BLOCKED — current mode "${getIntegrityMode()}" is not permitted. ` +
            'Only "offline-lab" and "training" modes allow screen capture.',
        );
        return null;
      }

      // TODO: Call native capture API when available.
      return {
        screenshot: 'mock-data',
        timestamp: Date.now(),
      };
    } catch (error) {
      console.error('[VisionAudioForge] captureScreen failed:', error);
      return null;
    }
  },

  // -----------------------------------------------------------------------
  // detectFormation
  // -----------------------------------------------------------------------

  /**
   * Detect the on-screen formation from image data. **Blocked** in
   * competitive modes (same policy as captureScreen).
   */
  async detectFormation(
    _imageData: ArrayBuffer | Blob | string,
  ): Promise<FormationDetection | null> {
    try {
      if (!isVisionAllowed()) {
        console.warn(
          `[VisionAudioForge] detectFormation BLOCKED — current mode "${getIntegrityMode()}" is not permitted. ` +
            'Only "offline-lab" and "training" modes allow formation detection.',
        );
        return null;
      }

      // TODO: POST image to VisionAudioForge REST API when available.
      return {
        formation: 'Cover 3',
        confidence: 94,
        blitzIndicators: false,
      };
    } catch (error) {
      console.error('[VisionAudioForge] detectFormation failed:', error);
      return null;
    }
  },

  // -----------------------------------------------------------------------
  // analyzeInputTelemetry
  // -----------------------------------------------------------------------

  /**
   * Analyse controller / input telemetry from recorded video data.
   * Always safe (post-game / non-competitive).
   */
  async analyzeInputTelemetry(
    _videoData: File | Blob | ArrayBuffer,
  ): Promise<InputTelemetry> {
    try {
      // TODO: POST to VisionAudioForge REST API when available.
      return {
        stickEfficiency: 78,
        overMovement: 12,
        inputTiming: 0.34,
        hesitationRate: 8,
      };
    } catch (error) {
      console.error(
        '[VisionAudioForge] analyzeInputTelemetry failed:',
        error,
      );
      return {
        stickEfficiency: 0,
        overMovement: 0,
        inputTiming: 0,
        hesitationRate: 0,
      };
    }
  },

  // -----------------------------------------------------------------------
  // exportClip
  // -----------------------------------------------------------------------

  /**
   * Export a video clip. Always safe (post-game utility).
   */
  async exportClip(
    _file: File | Blob | ArrayBuffer,
    opts?: ExportClipOptions,
  ): Promise<ClipExport> {
    try {
      // TODO: POST to VisionAudioForge REST API when available.
      return {
        url: 'mock-clip-url',
        format: opts?.format ?? 'mp4',
      };
    } catch (error) {
      console.error('[VisionAudioForge] exportClip failed:', error);
      return {
        url: '',
        format: opts?.format ?? 'mp4',
      };
    }
  },

  // -----------------------------------------------------------------------
  // isAvailable
  // -----------------------------------------------------------------------

  /**
   * Returns `true` when the service is reachable. Mock always returns true.
   */
  async isAvailable(): Promise<boolean> {
    try {
      // TODO: Health-check the VisionAudioForge REST API when available.
      return true;
    } catch {
      return false;
    }
  },
} as const;

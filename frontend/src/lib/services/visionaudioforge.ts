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

import api from '@/lib/api';
import { useUIStore } from '@/lib/store';
import type { DetectionConfig } from '@/lib/drills/drillDetectionConfigs';

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

/** Capture sources the user can configure. */
export type CaptureSource = 'capture-card' | 'pc-monitor' | 'camera';
const CAPTURE_SOURCE_KEY = 'visionSource';

/** Watching modes the monitor loop supports. */
export type DrillMonitorMode = 'simlab' | 'arsenal-practice' | 'drill-lab';

export interface FrameAnalysis {
  playInProgress: boolean;
  repCompleted: boolean;
  success: boolean | null;
  coverageDetected: string | null;
  playDetected: string | null;
  executionQuality: 'clean' | 'poor' | null;
  confidence: number;
  reason: string;
}

export interface StartDrillMonitoringOptions {
  mode: DrillMonitorMode;
  titleId: string;
  scenarioId?: string;
  weaponId?: string;
  weaponName?: string;
  formation?: string;
  playName?: string;
  detectionConfig: DetectionConfig;
  /** Called for every analysed frame, even when no rep is detected. */
  onFrameAnalyzed?: (analysis: FrameAnalysis) => void;
  /** Called when a rep is detected (success or fail). */
  onRepDetected: (analysis: FrameAnalysis) => void;
  /** Polling cadence in ms. Defaults to 2000. */
  pollIntervalMs?: number;
}

export interface DrillMonitoringHandle {
  stop: () => void;
}

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
 *
 * Practice contexts (SimLab, Arsenal Practice, Drill Lab) override this —
 * those are training-by-definition and always allowed regardless of the
 * sidebar's mode label.
 */
function isVisionAllowed(): boolean {
  return VISION_SAFE_MODES.has(getIntegrityMode());
}

/** Practice modes are always allowed — they're training, not live play. */
function isPracticeMonitoringAllowed(_mode: DrillMonitorMode): boolean {
  return true;
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

  // -----------------------------------------------------------------------
  // Capture source configuration
  // -----------------------------------------------------------------------

  getCaptureSource(): CaptureSource | null {
    try {
      if (typeof window === 'undefined') return null;
      const v = window.localStorage.getItem(CAPTURE_SOURCE_KEY);
      if (v === 'capture-card' || v === 'pc-monitor' || v === 'camera') return v;
      return null;
    } catch {
      return null;
    }
  },

  setCaptureSource(source: CaptureSource): void {
    try {
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(CAPTURE_SOURCE_KEY, source);
      }
      // Best-effort: persist to user settings on the server too.
      void api
        .patch('/users/me/settings', { vision_source: source })
        .catch(() => {
          // Endpoint may not exist yet — localStorage is the source of truth
          // until it does.
        });
    } catch {
      // Ignore.
    }
  },

  // -----------------------------------------------------------------------
  // Frame capture (placeholder — real implementation depends on the
  // configured capture source: HDMI capture card via DirectShow / OBS
  // virtual camera, browser screen-share, or webcam).
  // -----------------------------------------------------------------------

  async captureFrame(): Promise<{ base64: string } | null> {
    // The frame format the monitor endpoint expects is base64-encoded JPEG
    // without the data: prefix. Until a native capture path lands we return
    // a 1×1 transparent pixel so the polling loop still exercises the
    // endpoint contract.
    return {
      base64:
        '/9j/4AAQSkZJRgABAQEAAAAAAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAr/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A',
    };
  },

  // -----------------------------------------------------------------------
  // startDrillMonitoring — polling loop that captures frames, posts to the
  // monitor endpoint, and surfaces detected reps via callbacks.
  // -----------------------------------------------------------------------

  startDrillMonitoring(
    opts: StartDrillMonitoringOptions
  ): DrillMonitoringHandle {
    let stopped = false;
    const interval = opts.pollIntervalMs ?? 2000;

    const poll = async () => {
      while (!stopped) {
        try {
          if (!isPracticeMonitoringAllowed(opts.mode) && !isVisionAllowed()) {
            console.warn(
              '[VisionAudioForge] Drill monitoring not permitted in current mode.'
            );
            stopped = true;
            return;
          }

          const frame = await VisionAudioForgeService.captureFrame();
          if (!frame) {
            await wait(interval);
            continue;
          }

          const { data } = await api.post<FrameAnalysis>(
            '/drills/vision/monitor',
            {
              frame: frame.base64,
              mode: opts.mode,
              title_id: opts.titleId,
              scenario_id: opts.scenarioId,
              weapon_id: opts.weaponId,
              weapon_name: opts.weaponName,
              formation: opts.formation,
              play_name: opts.playName,
              detection: {
                type: opts.detectionConfig.type,
                watch_for: opts.detectionConfig.watchFor,
                success_criteria: opts.detectionConfig.successCriteria,
                fail_criteria: opts.detectionConfig.failCriteria,
                prompt_context: opts.detectionConfig.promptContext,
              },
            }
          );

          if (stopped) return;

          opts.onFrameAnalyzed?.(data);
          if (data.repCompleted) {
            opts.onRepDetected(data);
          }
        } catch (err) {
          // Endpoint missing key or transient failure — back off rather than
          // hammering. The UI surfaces a low-confidence indicator and the
          // manual override stays available.
          console.warn('[VisionAudioForge] monitor poll failed:', err);
        }
        await wait(interval);
      }
    };

    void poll();

    return {
      stop: () => {
        stopped = true;
      },
    };
  },
} as const;

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Active drill mode — full-page replacement for the queue/runner while a
 * drill is in flight.
 *
 * Manages the live DrillSession on the backend: starts on mount, posts each
 * rep, completes when all reps are logged or the player ends early.
 *
 * Manual ✓/✗ buttons are always visible. Auto-detection (VisionAudioForge)
 * is wired in a later commit via the optional `monitor` prop — the manual
 * path is the always-available fallback.
 */

'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Eye, Loader2, StopCircle } from 'lucide-react';
import { clsx } from 'clsx';
import type { DrillRecord } from '@/types/analytics';
import {
  completeDrillSession,
  recordDrillRep,
  startDrillSession,
  type DrillDebriefDTO,
} from '@/lib/api/drillSessions';
import RepTracker, { type RepDot } from './RepTracker';

export interface ActiveDrillResult {
  drill: DrillRecord;
  reps: RepDot[];
  debrief: DrillDebriefDTO;
}

export interface ActiveDrillMonitor {
  /** Status string surfaced to the player ("Watching…" / "Manual mode"). */
  label: string;
  /** Indicates whether vision detection is currently feeding events. */
  active: boolean;
}

interface ActiveDrillModeProps {
  drill: DrillRecord;
  titleId: string;
  /**
   * Optional vision-detection adapter. When present, ActiveDrillMode calls
   * `start({ onRep })` on mount and `stop()` on unmount. Passing nothing
   * keeps the experience in pure manual mode.
   */
  monitor?: {
    start: (args: {
      drill: DrillRecord;
      titleId: string;
      onRep: (success: boolean, confidence?: number, reason?: string) => void;
    }) => Promise<ActiveDrillMonitor> | ActiveDrillMonitor;
    stop: () => Promise<void> | void;
  };
  onComplete: (result: ActiveDrillResult) => void;
  onAbort: () => void;
}

export default function ActiveDrillMode({
  drill,
  titleId,
  monitor,
  onComplete,
  onAbort,
}: ActiveDrillModeProps) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [reps, setReps] = useState<RepDot[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [completing, setCompleting] = useState(false);
  const [monitorState, setMonitorState] = useState<ActiveDrillMonitor>({
    label: monitor ? 'Starting screen capture…' : 'Manual mode — tap a button to log each rep',
    active: false,
  });

  // currentRep = first 1-indexed rep that hasn't been logged yet.
  const currentRep = useMemo(() => {
    const logged = new Set(reps.filter((r) => r.status !== 'pending').map((r) => r.index));
    for (let i = 1; i <= drill.reps; i += 1) {
      if (!logged.has(i)) return i;
    }
    return drill.reps + 1; // overflow → completion path
  }, [reps, drill.reps]);

  const allDone = currentRep > drill.reps;

  // Keep the latest sessionId/currentRep available to vision callbacks.
  const sessionIdRef = useRef<string | null>(null);
  const currentRepRef = useRef<number>(1);
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);
  useEffect(() => {
    currentRepRef.current = currentRep;
  }, [currentRep]);

  // ----- start session on mount ------------------------------------------
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const sess = await startDrillSession({
          drillId: drill.id,
          drillType: drill.drillType,
          titleId,
          totalReps: drill.reps,
        });
        if (cancelled) return;
        setSessionId(sess.id);
      } catch (err) {
        console.error('[ActiveDrillMode] start failed', err);
        if (!cancelled) setError('Could not start drill session — check your connection.');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [drill.id, drill.drillType, drill.reps, titleId]);

  // ----- vision monitor lifecycle ----------------------------------------
  useEffect(() => {
    if (!monitor || !sessionId) return undefined;

    let stopped = false;
    (async () => {
      try {
        const status = await monitor.start({
          drill,
          titleId,
          onRep: (success, confidence, reason) => {
            void logRep({
              success,
              autoDetected: true,
              confidence,
              reason,
            });
          },
        });
        if (!stopped) setMonitorState(status);
      } catch (err) {
        console.warn('[ActiveDrillMode] monitor.start failed — falling back to manual mode', err);
        if (!stopped) {
          setMonitorState({
            label: 'Vision unavailable — manual mode active',
            active: false,
          });
        }
      }
    })();

    return () => {
      stopped = true;
      Promise.resolve(monitor.stop()).catch(() => {});
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monitor, sessionId]);

  // ----- core rep + completion logic -------------------------------------
  const logRep = useCallback(
    async (args: {
      success: boolean;
      autoDetected?: boolean;
      confidence?: number;
      reason?: string;
    }) => {
      const sid = sessionIdRef.current;
      const repNumber = currentRepRef.current;
      if (!sid || repNumber > drill.reps) return;

      // Optimistic: mark this rep, surface the result instantly.
      setReps((prev) => {
        if (prev.some((r) => r.index === repNumber && r.status !== 'pending')) {
          return prev;
        }
        const next = prev.filter((r) => r.index !== repNumber);
        next.push({
          index: repNumber,
          status: args.success ? 'success' : 'fail',
          autoDetected: args.autoDetected,
        });
        return next.sort((a, b) => a.index - b.index);
      });

      try {
        await recordDrillRep({
          sessionId: sid,
          repNumber,
          success: args.success,
          autoDetected: args.autoDetected,
          confidence: args.confidence,
          reason: args.reason,
        });
      } catch (err) {
        console.error('[ActiveDrillMode] recordRep failed', err);
        setError('Lost connection while logging the rep — using local state.');
      }
    },
    [drill.reps],
  );

  const finalize = useCallback(async () => {
    const sid = sessionIdRef.current;
    if (!sid || completing) return;
    setCompleting(true);
    try {
      const { debrief } = await completeDrillSession(sid);
      onComplete({ drill, reps, debrief });
    } catch (err) {
      console.error('[ActiveDrillMode] complete failed', err);
      setError('Could not finalize drill — try again.');
      setCompleting(false);
    }
  }, [completing, drill, reps, onComplete]);

  // Auto-complete when all reps are logged.
  useEffect(() => {
    if (allDone && sessionId && !completing) {
      void finalize();
    }
  }, [allDone, sessionId, completing, finalize]);

  // ----- render ----------------------------------------------------------
  return (
    <div className="space-y-5 rounded-xl border border-forge-500/30 bg-dark-900/60 p-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-forge-400">
            Drill active
          </p>
          <h2 className="mt-0.5 text-xl font-bold text-dark-50">{drill.name}</h2>
          <p className="mt-1 text-xs text-dark-400">
            Rep {Math.min(currentRep, drill.reps)} of {drill.reps} · IR {drill.impactRank}
          </p>
        </div>
        <button
          type="button"
          onClick={onAbort}
          className="inline-flex items-center gap-1.5 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs font-semibold text-red-300 hover:bg-red-500/20"
        >
          <StopCircle className="h-3.5 w-3.5" /> End drill early
        </button>
      </div>

      {/* Status */}
      <div
        className={clsx(
          'flex items-center gap-2 rounded-lg border px-3 py-2 text-xs',
          monitorState.active
            ? 'border-forge-500/30 bg-forge-500/10 text-forge-300'
            : 'border-dark-700/50 bg-dark-800/60 text-dark-300',
        )}
      >
        <Eye className="h-3.5 w-3.5" />
        <span>{monitorState.label}</span>
      </div>

      {/* Rep dots */}
      <RepTracker totalReps={drill.reps} reps={reps} />

      {/* Current rep instruction */}
      {!allDone && drill.objective && (
        <div className="rounded-lg bg-dark-800/40 px-4 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-dark-400">
            Current rep
          </p>
          <p className="mt-1 text-sm leading-relaxed text-dark-100">{drill.objective}</p>
        </div>
      )}

      {/* Manual override */}
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={!sessionId || allDone}
          onClick={() => void logRep({ success: true, autoDetected: false })}
          className="flex-1 rounded-lg bg-forge-500 px-4 py-2.5 text-sm font-bold text-dark-950 transition-colors hover:bg-forge-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          ✓ This rep worked
        </button>
        <button
          type="button"
          disabled={!sessionId || allDone}
          onClick={() => void logRep({ success: false, autoDetected: false })}
          className="flex-1 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-sm font-bold text-red-300 transition-colors hover:bg-red-500/20 disabled:cursor-not-allowed disabled:opacity-50"
        >
          ✗ This rep failed
        </button>
      </div>

      {error && (
        <p className="text-xs text-amber-400">{error}</p>
      )}

      {completing && (
        <p className="flex items-center gap-2 text-xs text-dark-400">
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
          Finalising session — generating LoopAI debrief…
        </p>
      )}
    </div>
  );
}

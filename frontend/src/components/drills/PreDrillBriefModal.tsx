/**
 * Pre-drill brief — shown after the player chooses a drill but before
 * VisionAudioForge starts watching. Surfaces objective, success/fail
 * criteria, and the "Go to your game" CTA.
 */

'use client';

import { Eye, Play, Sparkles, Target, Volume2, X } from 'lucide-react';
import { clsx } from 'clsx';
import type { DrillRecord } from '@/types/analytics';

interface PreDrillBriefModalProps {
  open: boolean;
  drill: DrillRecord | null;
  onStart: () => void;
  onCancel: () => void;
}

export default function PreDrillBriefModal({
  open,
  drill,
  onStart,
  onCancel,
}: PreDrillBriefModalProps) {
  if (!open || !drill) return null;

  const objective = drill.objective ?? drill.instructions;
  const successDef = drill.successDef ?? 'Completing the rep as instructed';
  const failDef = drill.failDef ?? 'Failing the rep — try again';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm px-4">
      <div className="relative w-full max-w-lg rounded-xl border border-forge-500/30 bg-dark-900 shadow-2xl">
        <button
          type="button"
          onClick={onCancel}
          className="absolute right-3 top-3 text-dark-500 hover:text-dark-200"
          aria-label="Cancel"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="border-b border-dark-700/50 px-6 py-4">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-forge-400">
            <Target className="h-4 w-4" />
            Starting drill
          </div>
          <h2 className="mt-1 text-xl font-bold text-dark-50">{drill.name}</h2>
          <div className="mt-2 flex items-center gap-3 text-xs text-dark-400">
            <span>{drill.reps} reps</span>
            <span className="text-dark-700">·</span>
            <span>IR {drill.impactRank}</span>
            {drill.isDynamicCalibration && (
              <>
                <span className="text-dark-700">·</span>
                <span className="inline-flex items-center gap-1 text-purple-400">
                  <Sparkles className="h-3 w-3" />
                  Dynamic calibration
                </span>
              </>
            )}
          </div>
        </div>

        <div className="space-y-4 px-6 py-5">
          <section>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-dark-400">
              Objective
            </p>
            <p className="mt-1 text-sm leading-relaxed text-dark-100">{objective}</p>
          </section>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-forge-500/20 bg-forge-500/5 px-3 py-2">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-forge-400">
                Success
              </p>
              <p className="mt-0.5 text-xs text-dark-200">{successDef}</p>
            </div>
            <div className="rounded-lg border border-red-500/20 bg-red-500/5 px-3 py-2">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-red-400">
                Fail
              </p>
              <p className="mt-0.5 text-xs text-dark-200">{failDef}</p>
            </div>
          </div>

          <div className="space-y-1.5 rounded-lg bg-dark-800/60 px-3 py-2 text-xs text-dark-300">
            <div className="flex items-center gap-2">
              <Volume2 className="h-3.5 w-3.5 text-sky-400" />
              <span>VoiceForge will coach you between reps.</span>
            </div>
            <div className="flex items-center gap-2">
              <Eye className="h-3.5 w-3.5 text-forge-400" />
              <span>VisionAudioForge will watch your screen and auto-mark reps.</span>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-dark-700/50 px-6 py-4">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg px-3 py-2 text-sm text-dark-300 hover:bg-dark-800 hover:text-dark-100"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onStart}
            className={clsx(
              'inline-flex items-center gap-2 rounded-lg bg-forge-500 px-4 py-2 text-sm font-bold text-dark-950',
              'shadow-lg shadow-forge-500/20 transition-colors hover:bg-forge-400',
            )}
          >
            <Play className="h-4 w-4 fill-current" />
            Start — go to your game
          </button>
        </div>
      </div>
    </div>
  );
}

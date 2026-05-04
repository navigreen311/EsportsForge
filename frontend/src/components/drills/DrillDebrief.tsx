/**
 * Post-drill debrief modal — fires automatically when all reps are complete.
 *
 * Insight payload comes from /drill-sessions/{id}/complete (deterministic
 * formula today; LoopAI vision/text wiring lives in a later commit).
 */

'use client';

import { useEffect } from 'react';
import { ArrowRight, Brain, CheckCircle2, Sparkles, X } from 'lucide-react';
import { clsx } from 'clsx';
import type { DrillRecord } from '@/types/analytics';
import type { DrillDebriefDTO } from '@/lib/api/drillSessions';
import { speakDebrief } from '@/lib/drills/voice';
import RepTracker, { type RepDot } from './RepTracker';

interface DrillDebriefProps {
  open: boolean;
  drill: DrillRecord | null;
  debrief: DrillDebriefDTO | null;
  reps: RepDot[];
  nextDrill: DrillRecord | null;
  onNext: () => void;
  onEnd: () => void;
}

const difficultyCopy: Record<DrillDebriefDTO['difficulty_recommendation'], { label: string; tone: string }> = {
  increase: { label: 'Difficulty advancing — more reps next session', tone: 'text-forge-400' },
  hold: { label: 'Same difficulty next session', tone: 'text-dark-200' },
  decrease: { label: 'Difficulty dialled back to rebuild rhythm', tone: 'text-amber-400' },
};

export default function DrillDebrief({
  open,
  drill,
  debrief,
  reps,
  nextDrill,
  onNext,
  onEnd,
}: DrillDebriefProps) {
  useEffect(() => {
    if (!open || !drill || !debrief) return;
    speakDebrief({
      drillName: drill.name,
      successReps: debrief.success_reps,
      totalReps: debrief.total_reps,
      insight: debrief.loop_ai_insight,
    });
  }, [open, drill, debrief]);

  if (!open || !drill || !debrief) return null;

  const difficultyInfo = difficultyCopy[debrief.difficulty_recommendation];
  const autoPct = Math.round(debrief.auto_detected_pct * 100);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm px-4">
      <div className="relative w-full max-w-xl rounded-xl border border-forge-500/30 bg-dark-900 shadow-2xl">
        <button
          type="button"
          onClick={onEnd}
          className="absolute right-3 top-3 text-dark-500 hover:text-dark-200"
          aria-label="Close debrief"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="border-b border-dark-700/50 px-6 py-4">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-forge-400">
            <CheckCircle2 className="h-4 w-4" />
            Drill complete — LoopAI feedback
          </div>
          <h2 className="mt-1 text-xl font-bold text-dark-50">{drill.name}</h2>
        </div>

        <div className="space-y-5 px-6 py-5">
          <section>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-dark-400">
              Performance
            </p>
            <div className="mt-2"><RepTracker totalReps={debrief.total_reps} reps={reps} /></div>
            <p className="mt-2 text-sm text-dark-200">
              <span className="font-bold text-forge-400">
                {debrief.success_reps}/{debrief.total_reps}
              </span>{' '}
              successful ({Math.round(debrief.success_rate * 100)}% success rate)
            </p>
            <p className="text-xs text-dark-500">
              Auto-detected {autoPct}% of reps
            </p>
          </section>

          <section className="rounded-lg border border-dark-700/50 bg-dark-800/60 px-4 py-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-400" />
              <p className="text-[10px] font-semibold uppercase tracking-wider text-purple-300">
                Skill update
              </p>
            </div>
            <p className="mt-1 text-sm text-dark-100">{debrief.skill_update}</p>
            <p className={clsx('mt-1 text-xs', difficultyInfo.tone)}>
              {difficultyInfo.label}
              {debrief.mastery_change !== 0 && (
                <span className="ml-2 font-semibold tabular-nums">
                  {debrief.mastery_change > 0 ? '+' : ''}
                  {debrief.mastery_change} mastery
                </span>
              )}
            </p>
          </section>

          <section className="rounded-lg border border-dark-700/50 bg-dark-800/60 px-4 py-3">
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-sky-400" />
              <p className="text-[10px] font-semibold uppercase tracking-wider text-sky-300">
                LoopAI insight
              </p>
            </div>
            <p className="mt-1 text-sm text-dark-100">{debrief.loop_ai_insight}</p>
            <p className="mt-2 text-[11px] italic text-dark-400">
              {debrief.player_twin_note}
            </p>
          </section>

          {nextDrill && (
            <section>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-dark-400">
                Next up
              </p>
              <p className="mt-1 text-sm font-semibold text-dark-100">
                {nextDrill.name}{' '}
                <span className="text-xs font-normal text-dark-500">
                  (IR {nextDrill.impactRank})
                </span>
              </p>
            </section>
          )}
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-dark-700/50 px-6 py-4">
          <button
            type="button"
            onClick={onEnd}
            className="rounded-lg px-3 py-2 text-sm text-dark-300 hover:bg-dark-800 hover:text-dark-100"
          >
            End session
          </button>
          {nextDrill && (
            <button
              type="button"
              onClick={onNext}
              className="inline-flex items-center gap-2 rounded-lg bg-forge-500 px-4 py-2 text-sm font-bold text-dark-950 transition-colors hover:bg-forge-400"
            >
              Next drill
              <ArrowRight className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

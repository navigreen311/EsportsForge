'use client';

import { Modal } from '@/components/shared/Modal';
import {
  Trophy,
  TrendingUp,
  RefreshCw,
  ArrowRight,
  Target,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';

interface PostDrillDebriefProps {
  open: boolean;
  onClose: () => void;
  onContinue: () => void;
  onEndSession: () => void;
  drillName: string;
  score: number;
  previousScore: number | null;
  /** Skills / areas that improved this drill. */
  improvements: string[];
  /** Areas to focus on next. */
  focusAreas: string[];
  /** PlayerTwin update description. */
  twinUpdate: string;
  nextDrillName: string | null;
}

/**
 * Enhanced post-drill debrief modal.
 * Shows: what improved, what to focus on, twin update, next recommendation.
 */
export default function PostDrillDebrief({
  open,
  onClose,
  onContinue,
  onEndSession,
  drillName,
  score,
  previousScore,
  improvements,
  focusAreas,
  twinUpdate,
  nextDrillName,
}: PostDrillDebriefProps) {
  const delta = previousScore !== null ? score - previousScore : null;
  const scoreDropped = delta !== null && delta < 0;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Post-Drill Debrief"
      size="lg"
    >
      <div className="space-y-5">
        {/* Performance Score */}
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-forge-500/10 border border-forge-800/30">
            <Trophy className="w-5 h-5 text-forge-400" />
          </div>
          <div>
            <p className="text-xs text-dark-400 uppercase tracking-wider">
              Performance — {drillName}
            </p>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-dark-50">
                {score}%
              </span>
              {delta !== null && (
                <span
                  className={`text-sm font-mono font-semibold ${
                    delta >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {delta >= 0 ? '+' : ''}
                  {delta} pts
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Fatigue warning */}
        {scoreDropped && (
          <div className="rounded-lg border border-amber-600/40 bg-amber-950/30 px-4 py-3 text-sm text-amber-300">
            Consider a break — fatigue may be affecting performance
          </div>
        )}

        {/* What Improved */}
        <div className="rounded-lg bg-dark-800/40 border border-dark-700/50 p-3">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="h-4 w-4 text-forge-400" />
            <p className="text-[10px] text-dark-500 uppercase tracking-wider font-bold">
              What Improved
            </p>
          </div>
          <div className="space-y-1.5">
            {improvements.map((item, i) => (
              <div key={i} className="flex items-start gap-2">
                <TrendingUp className="h-3.5 w-3.5 text-forge-400 mt-0.5 shrink-0" />
                <span className="text-sm text-dark-200">{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* What to Focus On */}
        <div className="rounded-lg bg-dark-800/40 border border-dark-700/50 p-3">
          <div className="flex items-center gap-2 mb-2">
            <Target className="h-4 w-4 text-amber-400" />
            <p className="text-[10px] text-dark-500 uppercase tracking-wider font-bold">
              Focus Areas
            </p>
          </div>
          <div className="space-y-1.5">
            {focusAreas.map((item, i) => (
              <div key={i} className="flex items-start gap-2">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-400 mt-0.5 shrink-0" />
                <span className="text-sm text-dark-200">{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Twin Update */}
        <div className="flex items-start gap-3 p-3 rounded-lg bg-purple-950/20 border border-purple-700/30">
          <RefreshCw className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-[10px] text-purple-400 uppercase tracking-wider">
              PlayerTwin Updated
            </p>
            <p className="text-sm text-purple-200">{twinUpdate}</p>
          </div>
        </div>

        {/* Next Recommendation */}
        <div className="flex items-center gap-3 p-3 rounded-lg bg-dark-800/40 border border-dark-700/50">
          <ArrowRight className="w-5 h-5 text-cyan-400 shrink-0" />
          <div>
            <p className="text-[10px] text-dark-500 uppercase tracking-wider">
              Next Recommendation
            </p>
            <p className="text-sm font-semibold text-dark-100">
              {nextDrillName ?? 'Session complete'}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={onContinue}
            disabled={nextDrillName === null}
            className="flex items-center gap-2 px-5 py-2.5 bg-forge-500 hover:bg-forge-600 disabled:opacity-40 disabled:cursor-not-allowed text-dark-950 font-bold rounded-lg transition-colors"
          >
            <ArrowRight className="w-4 h-4" />
            Continue to Next Drill
          </button>
          <button
            onClick={onEndSession}
            className="flex items-center gap-2 px-5 py-2.5 bg-dark-800 hover:bg-dark-700 border border-dark-600 text-dark-200 font-bold rounded-lg transition-colors"
          >
            End Session
          </button>
        </div>
      </div>
    </Modal>
  );
}

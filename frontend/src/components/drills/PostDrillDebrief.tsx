'use client';

import { useEffect, useState } from 'react';
import { Modal } from '@/components/shared/Modal';
import {
  Trophy,
  TrendingUp,
  RefreshCw,
  ArrowRight,
  Target,
  AlertTriangle,
  CheckCircle2,
  Film,
} from 'lucide-react';
import { AnimaPlayer } from '@/components/animaforge/AnimaPlayer';
import { useAnimaForgeAvailable } from '@/hooks/useAnimaForge';
import { animaforgeApi } from '@/lib/animaforge/api';
import { useActiveTitle } from '@/hooks/useActiveTitle';

interface PostDrillDebriefProps {
  open: boolean;
  onClose: () => void;
  onContinue: () => void;
  onEndSession: () => void;
  drillName: string;
  /**
   * Stable id of the drill — used to look up the cached AnimaForge demo
   * (same animation as the pre-drill brief, so users compare ideal vs reps).
   * Optional for backwards compatibility with existing callers.
   */
  drillId?: string;
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
  drillId,
  score,
  previousScore,
  improvements,
  focusAreas,
  twinUpdate,
  nextDrillName,
}: PostDrillDebriefProps) {
  const delta = previousScore !== null ? score - previousScore : null;
  const scoreDropped = delta !== null && delta < 0;

  // === AnimaForge: ideal-execution comparison =============================
  const { available: animaAvailable } = useAnimaForgeAvailable();
  const { activeTitleId } = useActiveTitle();
  const [showIdeal, setShowIdeal] = useState(false);
  const [idealVideoUrl, setIdealVideoUrl] = useState<string | null>(null);
  const [idealThumbnailUrl, setIdealThumbnailUrl] = useState<string | null>(
    null,
  );
  const [idealJobId, setIdealJobId] = useState<string | null>(null);
  const [idealLoading, setIdealLoading] = useState(false);

  // When the modal opens for a given drill, probe the cached demo so the
  // button can play it instantly (same source = same animation).
  useEffect(() => {
    if (!open || animaAvailable !== true || !drillId) return;
    let cancelled = false;
    animaforgeApi
      .getDrillStatus({ title_id: activeTitleId, drill_type: drillId })
      .then((data) => {
        if (cancelled) return;
        if (data.video_url) {
          setIdealVideoUrl(data.video_url);
          if (data.thumbnail_url) setIdealThumbnailUrl(data.thumbnail_url);
        } else if (data.job_id) {
          setIdealJobId(data.job_id);
        }
      })
      .catch(() => {
        // Stay silent.
      });
    return () => {
      cancelled = true;
    };
  }, [open, animaAvailable, activeTitleId, drillId]);

  const handleWatchIdeal = async () => {
    if (idealVideoUrl) {
      setShowIdeal(true);
      return;
    }
    if (!drillId) return;
    setIdealLoading(true);
    try {
      const data = await animaforgeApi.requestDrillRender({
        title_id: activeTitleId,
        drill_type: drillId,
        drill_name: drillName,
      });
      if (data.video_url) {
        setIdealVideoUrl(data.video_url);
        if (data.thumbnail_url) setIdealThumbnailUrl(data.thumbnail_url);
      } else if (data.job_id) {
        setIdealJobId(data.job_id);
      }
      setShowIdeal(true);
    } catch {
      // Silent.
    } finally {
      setIdealLoading(false);
    }
  };

  const showAnimaForgeUI = animaAvailable === true && !!drillId;
  // ========================================================================

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

        {/* AnimaForge: ideal execution comparison */}
        {showAnimaForgeUI && (
          <div className="rounded-lg border border-forge-700/30 bg-forge-950/10 p-3">
            <p className="text-xs text-forge-300 mb-2">
              Compare what perfect looks like vs your reps
            </p>
            <button
              onClick={handleWatchIdeal}
              disabled={idealLoading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-dark-800 hover:bg-dark-700 border border-forge-700/40 text-dark-100 text-sm font-medium transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <Film className="w-4 h-4 text-forge-400" />
              {idealLoading ? 'Loading…' : 'Watch Ideal Execution'}
            </button>
            {showIdeal && (idealVideoUrl || idealJobId) && (
              <div className="mt-3">
                <AnimaPlayer
                  jobId={idealJobId ?? undefined}
                  videoUrl={idealVideoUrl ?? undefined}
                  thumbnailUrl={idealThumbnailUrl ?? undefined}
                  type="drill-demo"
                  autoPlay
                  loop
                  onReady={(url) => setIdealVideoUrl(url)}
                />
              </div>
            )}
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

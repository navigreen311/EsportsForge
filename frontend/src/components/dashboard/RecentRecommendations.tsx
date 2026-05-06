/**
 * Last 5 agent recommendations with source badge, confidence, outcome,
 * and expandable proof layer ("Why?").
 *
 * FIX 7 — `Why?` evidence panel: when a recommendation has no proof bundle
 * we still show the toggle so the affordance is consistent, and the panel
 * renders a graceful "Evidence updates after your next session" placeholder
 * instead of empty rows.
 *
 * FIX 8 — Follow / Dismiss: when no follow/dismiss action has been taken
 * yet (`rec.followed` is undefined/null AND outcome === 'pending'), render
 * `[✓ Followed]` and `[✗ Dismissed]` buttons. On click the change is
 * applied optimistically, a toast confirms the action, and the backend is
 * notified asynchronously. Once an outcome is logged the static result
 * icon (current behaviour) is shown instead.
 */

'use client';

import { useState } from 'react';
import {
  Check,
  X,
  HelpCircle,
  ChevronDown,
  AlertTriangle,
  Database,
  FileText,
} from 'lucide-react';
import { clsx } from 'clsx';
import { Card } from '@/components/shared/Card';
import { Badge } from '@/components/shared/Badge';
import { ConfidenceBar } from '@/components/shared/ConfidenceBar';
import api from '@/lib/api';
import type { RecommendationItem } from '@/types/dashboard';

const outcomeConfig = {
  followed: {
    icon: Check,
    label: 'Followed',
    color: 'text-forge-400',
    bg: 'bg-forge-500/10',
  },
  ignored: {
    icon: X,
    label: 'Ignored',
    color: 'text-red-400',
    bg: 'bg-red-500/10',
  },
  pending: {
    icon: HelpCircle,
    label: 'Pending',
    color: 'text-dark-400',
    bg: 'bg-dark-700/50',
  },
} as const;

const agentVariant: Record<string, 'success' | 'info' | 'warning' | 'tier'> = {
  GameplanAgent: 'success',
  DrillCoach: 'info',
  OpponentScout: 'warning',
  SituationAnalyzer: 'tier',
};

interface RecentRecommendationsProps {
  recommendations: RecommendationItem[];
}

export default function RecentRecommendations({
  recommendations,
}: RecentRecommendationsProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  // Local follow/dismiss overrides — keyed by recommendation id so an
  // optimistic toggle survives across re-renders without mutating the
  // upstream prop array.
  const [localFollowed, setLocalFollowed] = useState<
    Record<string, boolean | null>
  >({});
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const postFeedback = async (
    id: string,
    action: 'followed' | 'dismissed'
  ) => {
    try {
      await api.post(`/recommendations/${id}/feedback`, { action });
    } catch (err) {
      // Network failure shouldn't undo the optimistic UX — LoopAI will
      // reconcile on the next dashboard fetch. Log for observability.
      // eslint-disable-next-line no-console
      console.warn('Recommendation feedback POST failed', err);
    }
  };

  const handleFollow = (id: string) => {
    setLocalFollowed((prev) => ({ ...prev, [id]: true }));
    showToast('LoopAI noted — model updating');
    void postFeedback(id, 'followed');
  };

  const handleDismiss = (id: string) => {
    setLocalFollowed((prev) => ({ ...prev, [id]: false }));
    void postFeedback(id, 'dismissed');
  };

  return (
    <Card padding="lg">
      <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-dark-300">
        Recent Recommendations
      </h3>

      <div className="divide-y divide-dark-700/50">
        {recommendations.map((rec) => {
          const outcome = outcomeConfig[rec.outcome];
          const OutcomeIcon = outcome.icon;
          const isExpanded = expandedId === rec.id;

          // Resolve effective follow state: local override wins, then the
          // value supplied by the upstream payload.
          const effectiveFollowed =
            rec.id in localFollowed ? localFollowed[rec.id] : rec.followed;
          const hasOutcome = rec.outcome !== 'pending';
          const showActionButtons =
            !hasOutcome &&
            (effectiveFollowed === undefined || effectiveFollowed === null);
          const isDimmed = effectiveFollowed === false && !hasOutcome;

          return (
            <div
              key={rec.id}
              className={clsx(
                'py-3 transition-opacity first:pt-0 last:pb-0',
                isDimmed && 'opacity-60'
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1 space-y-2">
                  {/* Agent badge + timestamp */}
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={agentVariant[rec.agentSource] ?? 'neutral'}
                      size="sm"
                    >
                      {rec.agentSource}
                    </Badge>
                    <span className="text-[10px] text-dark-500">
                      {rec.timestamp}
                    </span>
                  </div>

                  {/* Recommendation text */}
                  <p className="text-sm leading-relaxed text-dark-200">
                    {rec.text}
                  </p>

                  {/* Confidence bar */}
                  <ConfidenceBar
                    value={rec.confidence}
                    size="sm"
                    showValue
                    label="Confidence"
                  />

                  {/* Follow / Dismiss action buttons —
                      shown only when no outcome AND no follow action yet. */}
                  {showActionButtons && (
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleFollow(rec.id)}
                        className="inline-flex items-center gap-1 rounded-md border border-forge-500/40 bg-forge-500/10 px-2 py-1 text-[11px] font-medium text-forge-300 transition-colors hover:bg-forge-500/20 hover:text-forge-200"
                      >
                        <Check className="h-3 w-3" />
                        Followed
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDismiss(rec.id)}
                        className="inline-flex items-center gap-1 rounded-md border border-dark-600 bg-dark-800/50 px-2 py-1 text-[11px] font-medium text-dark-300 transition-colors hover:bg-dark-700 hover:text-dark-100"
                      >
                        <X className="h-3 w-3" />
                        Dismissed
                      </button>
                    </div>
                  )}

                  {/* Proof layer toggle — always available so the
                      affordance is consistent across the list. */}
                  <div>
                    <button
                      onClick={() =>
                        setExpandedId(isExpanded ? null : rec.id)
                      }
                      className="inline-flex items-center gap-1 text-[11px] font-medium text-dark-400 transition-colors hover:text-dark-200"
                    >
                      Why?
                      <ChevronDown
                        className={clsx(
                          'h-3 w-3 transition-transform',
                          isExpanded && 'rotate-180'
                        )}
                      />
                    </button>

                    {isExpanded && (
                      <div className="mt-2 space-y-1.5 rounded-lg border border-dark-700/50 bg-dark-800/50 px-3 py-2">
                        {rec.proof ? (
                          <>
                            <div className="flex items-start gap-1.5">
                              <FileText className="mt-0.5 h-3 w-3 flex-shrink-0 text-dark-500" />
                              <p className="text-[11px] text-dark-300">
                                <span className="font-medium text-dark-200">
                                  Reason:
                                </span>{' '}
                                {rec.proof.reason}
                              </p>
                            </div>
                            <div className="flex items-start gap-1.5">
                              <Database className="mt-0.5 h-3 w-3 flex-shrink-0 text-dark-500" />
                              <p className="text-[11px] text-dark-300">
                                <span className="font-medium text-dark-200">
                                  Data:
                                </span>{' '}
                                {rec.proof.dataSource}
                              </p>
                            </div>
                            <div className="flex items-start gap-1.5">
                              <AlertTriangle className="mt-0.5 h-3 w-3 flex-shrink-0 text-amber-500" />
                              <p className="text-[11px] text-dark-300">
                                <span className="font-medium text-amber-400">
                                  Risk:
                                </span>{' '}
                                {rec.proof.riskIfIgnored}
                              </p>
                            </div>
                          </>
                        ) : (
                          <p className="text-[11px] italic text-dark-400">
                            Evidence updates after your next session
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Outcome indicator — preserves existing display logic. */}
                <div
                  className={clsx(
                    'flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full',
                    outcome.bg
                  )}
                  title={outcome.label}
                >
                  <OutcomeIcon className={clsx('h-4 w-4', outcome.color)} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {toastMessage && (
        <div
          role="status"
          aria-live="polite"
          className="pointer-events-none fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-md border border-forge-500/40 bg-dark-800/95 px-3 py-2 text-[12px] font-medium text-forge-200 shadow-lg"
        >
          {toastMessage}
        </div>
      )}
    </Card>
  );
}

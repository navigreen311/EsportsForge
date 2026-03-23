/**
 * Last 5 agent recommendations with source badge, confidence, outcome,
 * and expandable proof layer ("Why?").
 */

'use client';

import { useState } from 'react';
import { Check, X, HelpCircle, ChevronDown, AlertTriangle, Database, FileText } from 'lucide-react';
import { clsx } from 'clsx';
import { Card } from '@/components/shared/Card';
import { Badge } from '@/components/shared/Badge';
import { ConfidenceBar } from '@/components/shared/ConfidenceBar';
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

          return (
            <div key={rec.id} className="py-3 first:pt-0 last:pb-0">
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

                  {/* Proof layer toggle */}
                  {rec.proof && (
                    <div>
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : rec.id)}
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
                          <div className="flex items-start gap-1.5">
                            <FileText className="mt-0.5 h-3 w-3 flex-shrink-0 text-dark-500" />
                            <p className="text-[11px] text-dark-300">
                              <span className="font-medium text-dark-200">Reason:</span>{' '}
                              {rec.proof.reason}
                            </p>
                          </div>
                          <div className="flex items-start gap-1.5">
                            <Database className="mt-0.5 h-3 w-3 flex-shrink-0 text-dark-500" />
                            <p className="text-[11px] text-dark-300">
                              <span className="font-medium text-dark-200">Data:</span>{' '}
                              {rec.proof.dataSource}
                            </p>
                          </div>
                          <div className="flex items-start gap-1.5">
                            <AlertTriangle className="mt-0.5 h-3 w-3 flex-shrink-0 text-amber-500" />
                            <p className="text-[11px] text-dark-300">
                              <span className="font-medium text-amber-400">Risk:</span>{' '}
                              {rec.proof.riskIfIgnored}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Outcome indicator */}
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
    </Card>
  );
}

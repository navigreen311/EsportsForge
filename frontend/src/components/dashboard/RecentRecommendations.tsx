/**
 * Last 5 agent recommendations with source badge, confidence, and outcome.
 */

'use client';

import { Check, X, HelpCircle } from 'lucide-react';
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
  return (
    <Card padding="lg">
      <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-dark-300">
        Recent Recommendations
      </h3>

      <div className="divide-y divide-dark-700/50">
        {recommendations.map((rec) => {
          const outcome = outcomeConfig[rec.outcome];
          const OutcomeIcon = outcome.icon;

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

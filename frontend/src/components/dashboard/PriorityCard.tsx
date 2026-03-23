/**
 * Large priority weakness card — shows the #1 thing to fix with
 * impact rank, win-rate damage, expected lift, and a CTA.
 */

'use client';

import { Brain, Shield, Swords, Zap, ArrowRight } from 'lucide-react';
import { clsx } from 'clsx';
import { Card } from '@/components/shared/Card';
import { ConfidenceBar } from '@/components/shared/ConfidenceBar';
import type { PriorityItem } from '@/types/dashboard';

const categoryConfig: Record<
  PriorityItem['category'],
  { icon: typeof Brain; color: string; label: string }
> = {
  mental: { icon: Brain, color: 'text-purple-400', label: 'Mental' },
  defense: { icon: Shield, color: 'text-sky-400', label: 'Defense' },
  offense: { icon: Swords, color: 'text-orange-400', label: 'Offense' },
  situational: { icon: Zap, color: 'text-amber-400', label: 'Situational' },
};

interface PriorityCardProps {
  priority: PriorityItem;
}

export default function PriorityCard({ priority }: PriorityCardProps) {
  const cat = categoryConfig[priority.category];
  const CategoryIcon = cat.icon;

  return (
    <Card padding="lg" className="relative overflow-hidden">
      {/* Subtle gradient accent */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-forge-500/5 via-transparent to-transparent" />

      <div className="relative space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className={clsx(
                'flex h-10 w-10 items-center justify-center rounded-lg bg-dark-800',
                cat.color
              )}
            >
              <CategoryIcon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-dark-400">
                #1 Priority — {cat.label}
              </p>
              <h3 className="text-lg font-bold text-dark-50">
                {priority.weakness}
              </h3>
            </div>
          </div>

          {/* Impact Rank */}
          <div className="flex flex-col items-center rounded-lg border border-forge-500/30 bg-forge-500/10 px-3 py-2">
            <span className="text-[10px] font-medium uppercase tracking-wider text-forge-400">
              Impact
            </span>
            <span className="text-2xl font-black tabular-nums text-forge-400">
              {priority.impactRank}
            </span>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <div>
            <p className="text-xs text-dark-500">Win-Rate Damage</p>
            <p className="text-xl font-bold tabular-nums text-red-400">
              -{priority.winRateDamage}%
            </p>
          </div>
          <div>
            <p className="text-xs text-dark-500">Expected Lift</p>
            <p className="text-xl font-bold tabular-nums text-forge-400">
              +{priority.expectedLift}%
            </p>
          </div>
          <div className="col-span-2 sm:col-span-1">
            <p className="text-xs text-dark-500">Time to Master</p>
            <p className="text-xl font-bold text-dark-200">
              {priority.timeToMaster}
            </p>
          </div>
        </div>

        {/* Confidence */}
        <ConfidenceBar
          value={priority.confidence}
          label="AI Confidence"
          size="md"
        />

        {/* CTA */}
        <button
          type="button"
          className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-forge-500 px-4 py-2.5 text-sm font-bold text-dark-950 transition-colors hover:bg-forge-400 sm:w-auto"
        >
          Start Fixing
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </Card>
  );
}

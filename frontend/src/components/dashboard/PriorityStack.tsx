/**
 * ImpactRank Priority Stack — shows #2 and #3 priorities as collapsible items.
 */

'use client';

import { useState } from 'react';
import { ChevronDown, Brain, Shield, Swords, Zap } from 'lucide-react';
import { clsx } from 'clsx';
import { Card } from '@/components/shared/Card';
import { ConfidenceBar } from '@/components/shared/ConfidenceBar';
import type { PriorityItem } from '@/types/dashboard';

const categoryIcons: Record<PriorityItem['category'], typeof Brain> = {
  mental: Brain,
  defense: Shield,
  offense: Swords,
  situational: Zap,
};

const categoryColors: Record<PriorityItem['category'], string> = {
  mental: 'text-purple-400',
  defense: 'text-sky-400',
  offense: 'text-orange-400',
  situational: 'text-amber-400',
};

interface PriorityStackProps {
  priorities: PriorityItem[];
}

export default function PriorityStack({ priorities }: PriorityStackProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Show only #2 and #3 (skip #1 which is already displayed by PriorityCard)
  const secondary = priorities.slice(1, 3);
  if (secondary.length === 0) return null;

  return (
    <div className="space-y-2">
      <p className="text-[10px] font-medium uppercase tracking-wider text-dark-500">
        Next priorities
      </p>
      {secondary.map((item, idx) => {
        const rank = idx + 2;
        const Icon = categoryIcons[item.category];
        const color = categoryColors[item.category];
        const isExpanded = expandedId === item.id;

        return (
          <Card key={item.id} padding="none">
            <button
              onClick={() => setExpandedId(isExpanded ? null : item.id)}
              className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-dark-800/50"
            >
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-dark-800 text-xs font-black text-dark-300">
                #{rank}
              </span>
              <Icon className={clsx('h-4 w-4', color)} />
              <span className="min-w-0 flex-1 truncate text-sm font-medium text-dark-200">
                {item.weakness}
              </span>
              <span className="rounded-md border border-forge-500/30 bg-forge-500/10 px-2 py-0.5 text-xs font-bold tabular-nums text-forge-400">
                {item.impactRank}
              </span>
              <ChevronDown
                className={clsx(
                  'h-4 w-4 text-dark-500 transition-transform',
                  isExpanded && 'rotate-180'
                )}
              />
            </button>

            {isExpanded && (
              <div className="space-y-3 border-t border-dark-700/50 px-4 py-3">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-dark-500">Win-Rate Damage</p>
                    <p className="text-lg font-bold tabular-nums text-red-400">
                      -{item.winRateDamage}%
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-dark-500">Expected Lift</p>
                    <p className="text-lg font-bold tabular-nums text-forge-400">
                      +{item.expectedLift}%
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-dark-500">Time to Master</p>
                    <p className="text-lg font-bold text-dark-200">
                      {item.timeToMaster}
                    </p>
                  </div>
                </div>
                <ConfidenceBar
                  value={item.confidence}
                  label="AI Confidence"
                  size="sm"
                />
              </div>
            )}
          </Card>
        );
      })}
    </div>
  );
}

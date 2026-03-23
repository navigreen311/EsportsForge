/**
 * BenchmarkAI percentile panel — 2x2 grid of player percentile rankings.
 */

'use client';

import { clsx } from 'clsx';
import { BarChart3 } from 'lucide-react';
import { Card } from '@/components/shared/Card';
import type { BenchmarkMetric } from '@/types/dashboard';

function getPercentileStyle(percentile: number) {
  if (percentile >= 75) return { text: 'text-forge-400', bar: 'bg-forge-500', badge: 'text-forge-400' };
  if (percentile >= 40) return { text: 'text-amber-400', bar: 'bg-amber-500', badge: 'text-amber-400' };
  return { text: 'text-dark-400', bar: 'bg-dark-500', badge: 'text-dark-400' };
}

interface BenchmarkPanelProps {
  benchmarks: BenchmarkMetric[];
}

export default function BenchmarkPanel({ benchmarks }: BenchmarkPanelProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <BarChart3 className="h-4 w-4 text-dark-400" />
        <h3 className="text-sm font-bold uppercase tracking-wider text-dark-300">
          Your Percentile Rank
        </h3>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {benchmarks.map((metric) => {
          const style = getPercentileStyle(metric.percentile);
          return (
            <Card key={metric.label} padding="sm">
              <p className="mb-1 text-[11px] font-medium text-dark-400">
                {metric.label}
              </p>
              <p className={clsx('text-lg font-black tabular-nums', style.badge)}>
                Top {100 - metric.percentile}%
              </p>
              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-dark-800">
                <div
                  className={clsx('h-full rounded-full transition-all duration-500', style.bar)}
                  style={{ width: `${metric.percentile}%` }}
                />
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

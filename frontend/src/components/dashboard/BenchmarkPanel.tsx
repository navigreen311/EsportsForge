/**
 * BenchmarkAI percentile panel — 2x2 grid of player percentile rankings.
 *
 * Each card is a link to /analytics?skill=<slug> so users can drill into the
 * underlying skill view. Slugs for the canonical 5 metrics are mapped
 * explicitly; any other label falls back to a lowercased / hyphenated slug.
 */

'use client';

import Link from 'next/link';
import { clsx } from 'clsx';
import { BarChart3 } from 'lucide-react';
import { Card } from '@/components/shared/Card';
import type { BenchmarkMetric } from '@/types/dashboard';

function getPercentileStyle(percentile: number) {
  if (percentile >= 75) return { text: 'text-forge-400', bar: 'bg-forge-500', badge: 'text-forge-400' };
  if (percentile >= 40) return { text: 'text-amber-400', bar: 'bg-amber-500', badge: 'text-amber-400' };
  return { text: 'text-dark-400', bar: 'bg-dark-500', badge: 'text-dark-400' };
}

const SKILL_SLUGS: Record<string, string> = {
  'Win Rate': 'win-rate',
  'Read Speed': 'read-speed',
  'Red Zone': 'red-zone',
  'Clutch': 'clutch',
  'Adaptation': 'adaptation',
};

function toSlug(label: string): string {
  if (SKILL_SLUGS[label]) return SKILL_SLUGS[label];
  return label
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
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
          const slug = toSlug(metric.label);
          const tooltip = `Top ${metric.percentile}% means you outperform ${100 - metric.percentile}% of players in your tier on ${metric.label}`;
          return (
            <Link
              key={metric.label}
              href={`/analytics?skill=${slug}`}
              title={tooltip}
              aria-label={tooltip}
              className="block rounded-xl transition-transform hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-forge-500/40"
            >
              <Card padding="sm">
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
            </Link>
          );
        })}
      </div>
    </div>
  );
}

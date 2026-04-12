'use client';

import { BarChart3, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface BenchmarkMetric {
  label: string;
  percentile: number;
  delta: number;
  tier: 'Elite' | 'Advanced' | 'Competitive' | 'Developing';
}

const metrics: BenchmarkMetric[] = [
  { label: 'Read Speed', percentile: 72, delta: 3, tier: 'Advanced' },
  { label: 'Clutch Conversion', percentile: 34, delta: -1, tier: 'Developing' },
  { label: 'User Defense', percentile: 58, delta: 2, tier: 'Competitive' },
  { label: 'Execution Under Pressure', percentile: 81, delta: 5, tier: 'Advanced' },
  { label: 'Anti-Meta Adaptability', percentile: 45, delta: 0, tier: 'Competitive' },
  { label: 'Red Zone Efficiency', percentile: 67, delta: 4, tier: 'Advanced' },
  { label: 'Clock Management', percentile: 52, delta: -2, tier: 'Competitive' },
  { label: 'Blitz Recognition', percentile: 39, delta: 1, tier: 'Developing' },
];

const tierStyles: Record<BenchmarkMetric['tier'], { text: string; bg: string }> = {
  Elite: { text: 'text-forge-400', bg: 'bg-forge-500/10' },
  Advanced: { text: 'text-cyan-400', bg: 'bg-cyan-500/10' },
  Competitive: { text: 'text-amber-400', bg: 'bg-amber-500/10' },
  Developing: { text: 'text-dark-400', bg: 'bg-dark-700/50' },
};

function DeltaIndicator({ delta }: { delta: number }) {
  if (delta > 0) {
    return (
      <span className="flex items-center gap-0.5 text-xs text-green-400">
        <TrendingUp className="h-3 w-3" />
        +{delta}
      </span>
    );
  }
  if (delta < 0) {
    return (
      <span className="flex items-center gap-0.5 text-xs text-red-400">
        <TrendingDown className="h-3 w-3" />
        {delta}
      </span>
    );
  }
  return (
    <span className="flex items-center gap-0.5 text-xs text-dark-400">
      <Minus className="h-3 w-3" />
      &mdash;
    </span>
  );
}

function PercentileBar({ percentile, tierText }: { percentile: number; tierText: string }) {
  const barColor =
    percentile >= 75
      ? 'bg-cyan-400'
      : percentile >= 50
        ? 'bg-amber-400'
        : percentile >= 25
          ? 'bg-dark-400'
          : 'bg-red-400';

  return (
    <div className="relative mt-2 h-2 w-full rounded-full bg-dark-700">
      <div
        className={`h-2 rounded-full transition-all duration-700 ${barColor}`}
        style={{ width: `${percentile}%` }}
      />
      {/* Position marker */}
      <div
        className={`absolute top-1/2 h-3.5 w-3.5 -translate-y-1/2 rounded-full border-2 border-dark-800 ${barColor}`}
        style={{ left: `${percentile}%`, transform: 'translate(-50%, -50%)' }}
      />
    </div>
  );
}

function MetricCard({ metric }: { metric: BenchmarkMetric }) {
  const style = tierStyles[metric.tier];
  const topPercent = 100 - metric.percentile;

  return (
    <div className="rounded-lg border border-dark-700/50 bg-dark-800/50 p-3">
      <p className="mb-1 text-xs text-dark-400 truncate" title={metric.label}>
        {metric.label}
      </p>
      <p className="text-2xl font-bold text-white">Top {topPercent}%</p>

      <PercentileBar percentile={metric.percentile} tierText={style.text} />

      <div className="mt-2 flex items-center justify-between">
        <DeltaIndicator delta={metric.delta} />
        <span
          className={`rounded px-1.5 py-0.5 text-xs font-medium ${style.text} ${style.bg}`}
        >
          {metric.tier}
        </span>
      </div>
    </div>
  );
}

/**
 * BenchmarkSection with 8 metrics and percentile bars.
 * Enhanced version with full percentile bar fills.
 */
export default function BenchmarkSection() {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="mb-4 flex items-center gap-2">
        <BarChart3 className="h-5 w-5 text-forge-400" />
        <h2 className="text-lg font-semibold text-white">
          BenchmarkAI Competitive Rank
        </h2>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </div>

      <p className="mt-4 text-sm text-forge-400">
        Overall Rank: Top 28% of Madden 26 competitive players
      </p>
    </div>
  );
}

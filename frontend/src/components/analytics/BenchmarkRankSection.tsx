"use client";

import { BarChart3, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface BenchmarkMetric {
  label: string;
  percentile: number;
  delta: number;
  tier: "Elite" | "Advanced" | "Competitive" | "Developing";
}

const metrics: BenchmarkMetric[] = [
  { label: "Read Speed", percentile: 72, delta: 3, tier: "Advanced" },
  { label: "Clutch Conversion", percentile: 34, delta: -1, tier: "Developing" },
  { label: "User Defense", percentile: 58, delta: 2, tier: "Competitive" },
  { label: "Execution Under Pressure", percentile: 81, delta: 5, tier: "Advanced" },
  { label: "Anti-Meta Adaptability", percentile: 45, delta: 0, tier: "Competitive" },
];

const tierStyles: Record<
  BenchmarkMetric["tier"],
  { text: string; bg: string }
> = {
  Elite: { text: "text-forge-400", bg: "bg-forge-500/10" },
  Advanced: { text: "text-cyan-400", bg: "bg-cyan-500/10" },
  Competitive: { text: "text-amber-400", bg: "bg-amber-500/10" },
  Developing: { text: "text-dark-400", bg: "bg-dark-700/50" },
};

function getTierFromPercentile(percentile: number): BenchmarkMetric["tier"] {
  if (percentile >= 90) return "Elite";
  if (percentile >= 75) return "Advanced";
  if (percentile >= 40) return "Competitive";
  return "Developing";
}

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

function MetricCard({ metric }: { metric: BenchmarkMetric }) {
  const style = tierStyles[metric.tier];
  const topPercent = 100 - metric.percentile;

  return (
    <div className="rounded-lg border border-dark-700/50 bg-dark-800/50 p-3">
      <p className="mb-2 text-xs text-dark-400">{metric.label}</p>

      <p className="text-2xl font-bold text-white">
        Top {topPercent}%
      </p>

      {/* Percentile bar */}
      <div className="relative mt-2 h-1.5 w-full rounded-full bg-dark-700">
        <div
          className={`absolute top-1/2 h-3 w-3 -translate-y-1/2 rounded-full border-2 border-dark-800 ${style.text.replace("text-", "bg-")}`}
          style={{ left: `${metric.percentile}%` }}
        />
      </div>

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

export default function BenchmarkRankSection() {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="mb-4 flex items-center gap-2">
        <BarChart3 className="h-5 w-5 text-forge-400" />
        <h2 className="text-lg font-semibold text-white">
          Your Competitive Rank
        </h2>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
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

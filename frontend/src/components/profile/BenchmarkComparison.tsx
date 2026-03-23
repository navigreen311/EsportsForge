'use client';

import { BenchmarkEntry } from '@/hooks/useProfile';
import { BarChart3 } from 'lucide-react';

interface BenchmarkComparisonProps {
  benchmarks: BenchmarkEntry[];
}

export default function BenchmarkComparison({
  benchmarks,
}: BenchmarkComparisonProps) {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <h2 className="text-lg font-bold text-dark-100 mb-1 flex items-center gap-2">
        <BarChart3 className="w-5 h-5 text-cyan-400" />
        Benchmark Comparison
      </h2>
      <p className="text-xs text-dark-500 mb-4">You vs Top 5% players</p>

      <div className="space-y-4">
        {benchmarks.map((bench) => {
          const gap = bench.top5Percent - bench.player;
          return (
            <div key={bench.skill}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-dark-200">
                  {bench.skill}
                </span>
                <span className="text-[10px] font-mono text-dark-500">
                  Gap: {gap}
                </span>
              </div>

              {/* Overlay bars */}
              <div className="relative w-full bg-dark-800 rounded-full h-3">
                {/* Top 5% bar (background, wider) */}
                <div
                  className="absolute top-0 h-3 rounded-full bg-cyan-500/20 border border-cyan-500/30"
                  style={{ width: `${bench.top5Percent}%` }}
                />
                {/* Player bar (foreground) */}
                <div
                  className="absolute top-0 h-3 rounded-full bg-gradient-to-r from-forge-600 to-forge-400"
                  style={{ width: `${bench.player}%` }}
                />
              </div>

              {/* Values */}
              <div className="flex justify-between mt-1">
                <span className="text-[10px] font-mono text-forge-400">
                  You: {bench.player}
                </span>
                <span className="text-[10px] font-mono text-cyan-400">
                  Top 5%: {bench.top5Percent}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-5 pt-3 border-t border-dark-700/50">
        <span className="flex items-center gap-1.5 text-xs text-dark-400">
          <span className="w-3 h-2 rounded bg-forge-500" /> Your Rating
        </span>
        <span className="flex items-center gap-1.5 text-xs text-dark-400">
          <span className="w-3 h-2 rounded bg-cyan-500/30 border border-cyan-500/50" />{' '}
          Top 5%
        </span>
      </div>
    </div>
  );
}

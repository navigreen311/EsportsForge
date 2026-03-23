'use client';

import { WeaknessHeatmapEntry } from '@/types/analytics';

interface WeaknessHeatmapProps {
  data: WeaknessHeatmapEntry[];
}

const categoryColors: Record<string, string> = {
  offense: 'border-l-blue-500',
  defense: 'border-l-red-500',
  situational: 'border-l-yellow-500',
  mental: 'border-l-purple-500',
};

function getHeatColor(impactRank: number, currentLevel: number): string {
  const gap = 100 - currentLevel;
  const severity = (impactRank / 10) * (gap / 100);
  if (severity > 0.5) return 'bg-red-500/30 border-red-800/50';
  if (severity > 0.3) return 'bg-orange-500/20 border-orange-800/50';
  if (severity > 0.15) return 'bg-yellow-500/15 border-yellow-800/50';
  return 'bg-forge-500/10 border-forge-800/50';
}

export default function WeaknessHeatmap({ data }: WeaknessHeatmapProps) {
  const sorted = [...data].sort((a, b) => b.impactRank - a.impactRank);

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-dark-100">Weakness Heatmap</h2>
          <p className="text-sm text-dark-400">ImpactRank priority</p>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-dark-500">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-red-500/30" /> Critical
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-orange-500/20" /> High
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-yellow-500/15" /> Medium
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-forge-500/10" /> Low
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {sorted.map((entry) => (
          <div
            key={entry.skill}
            className={`rounded-lg border p-3 border-l-4 ${categoryColors[entry.category]} ${getHeatColor(entry.impactRank, entry.currentLevel)}`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-dark-100">{entry.skill}</span>
              <span className="text-xs font-mono text-dark-400">
                IR: {entry.impactRank}
              </span>
            </div>
            <div className="w-full bg-dark-800 rounded-full h-2 mb-1">
              <div
                className="h-2 rounded-full bg-forge-500 transition-all duration-500"
                style={{ width: `${entry.currentLevel}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-dark-500">
              <span>Current: {entry.currentLevel}</span>
              <span>Target: {entry.targetLevel}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

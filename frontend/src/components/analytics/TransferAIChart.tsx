'use client';

import { ArrowRightLeft, AlertTriangle } from 'lucide-react';

interface TransferSkill {
  skill: string;
  labScore: number;
  liveScore: number;
  gap: number;
  trend: 'improving' | 'stable' | 'widening';
}

const MOCK_SKILLS: TransferSkill[] = [
  { skill: 'Read Speed', labScore: 85, liveScore: 62, gap: 23, trend: 'improving' },
  { skill: 'Execution', labScore: 88, liveScore: 71, gap: 17, trend: 'stable' },
  { skill: 'Clutch', labScore: 72, liveScore: 31, gap: 41, trend: 'widening' },
  { skill: 'Anti-Meta', labScore: 68, liveScore: 42, gap: 26, trend: 'improving' },
  { skill: 'Mental', labScore: 79, liveScore: 52, gap: 27, trend: 'stable' },
  { skill: 'Game Knowledge', labScore: 91, liveScore: 68, gap: 23, trend: 'improving' },
];

function gapColor(gap: number): string {
  if (gap <= 15) return 'text-forge-400';
  if (gap <= 25) return 'text-amber-400';
  return 'text-red-400';
}

function gapBg(gap: number): string {
  if (gap <= 15) return 'bg-forge-500/10 border-forge-800/30';
  if (gap <= 25) return 'bg-amber-500/10 border-amber-800/30';
  return 'bg-red-500/10 border-red-800/30';
}

function trendLabel(trend: TransferSkill['trend']): { text: string; color: string } {
  switch (trend) {
    case 'improving':
      return { text: 'Closing', color: 'text-forge-400' };
    case 'stable':
      return { text: 'Stable', color: 'text-dark-400' };
    case 'widening':
      return { text: 'Widening', color: 'text-red-400' };
  }
}

/**
 * Lab vs Live performance comparison chart for analytics.
 * Shows side-by-side bars with gap indicators.
 */
export default function TransferAIChart() {
  const avgGap = Math.round(
    MOCK_SKILLS.reduce((sum, s) => sum + s.gap, 0) / MOCK_SKILLS.length,
  );

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <ArrowRightLeft className="h-5 w-5 text-cyan-400" />
          <div>
            <h2 className="text-lg font-semibold text-white">
              TransferAI Lab vs Live
            </h2>
            <p className="text-sm text-dark-400">
              Avg gap: <span className={`font-bold ${gapColor(avgGap)}`}>{avgGap}pts</span>
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {MOCK_SKILLS.map((skill) => {
          const trend = trendLabel(skill.trend);

          return (
            <div key={skill.skill} className="rounded-lg bg-dark-800/30 border border-dark-700/50 p-3">
              {/* Header row */}
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-dark-200">{skill.skill}</span>
                <div className="flex items-center gap-3">
                  <span className={`text-xs ${trend.color}`}>{trend.text}</span>
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold border ${gapBg(skill.gap)} ${gapColor(skill.gap)}`}
                  >
                    {skill.gap > 25 && <AlertTriangle className="h-3 w-3" />}
                    -{skill.gap}pts
                  </span>
                </div>
              </div>

              {/* Lab bar */}
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] text-dark-500 w-8 shrink-0">Lab</span>
                <div className="flex-1 h-2.5 rounded-full bg-dark-700">
                  <div
                    className="h-2.5 rounded-full bg-forge-400 transition-all duration-500"
                    style={{ width: `${skill.labScore}%` }}
                  />
                </div>
                <span className="text-xs font-mono text-dark-300 w-10 text-right">
                  {skill.labScore}%
                </span>
              </div>

              {/* Live bar */}
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-dark-500 w-8 shrink-0">Live</span>
                <div className="flex-1 h-2.5 rounded-full bg-dark-700">
                  <div
                    className={`h-2.5 rounded-full transition-all duration-500 ${
                      skill.gap <= 15
                        ? 'bg-forge-500'
                        : skill.gap <= 25
                          ? 'bg-amber-500'
                          : 'bg-red-500'
                    }`}
                    style={{ width: `${skill.liveScore}%` }}
                  />
                </div>
                <span className="text-xs font-mono text-dark-300 w-10 text-right">
                  {skill.liveScore}%
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center gap-6 text-xs text-dark-400">
        <div className="flex items-center gap-2">
          <span className="inline-block w-3 h-2 rounded bg-forge-400" />
          <span>Lab Performance</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block w-3 h-2 rounded bg-amber-500" />
          <span>Live Performance</span>
        </div>
      </div>
    </div>
  );
}

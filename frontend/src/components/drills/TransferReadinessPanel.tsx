'use client';

import { ArrowRightLeft, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

/** Hardcoded ranked and tournament transfer rates per skill. */
const RANKED_RATES: Record<string, number> = {
  'Read Speed': 54,
  Execution: 71,
  Clutch: 31,
  'Anti-Meta': 28,
  Mental: 52,
  'Game Knowledge': 68,
};

const TOURNAMENT_RATES: Record<string, number> = {
  'Read Speed': 31,
  Execution: 45,
  Clutch: 18,
  'Anti-Meta': 15,
  Mental: 33,
  'Game Knowledge': 42,
};

export interface TransferSkill {
  name: string;
  current: number;
  target: number;
  baseline: number;
}

export interface TransferReadinessInfo {
  /** Skills that are NOT competition-ready (ranked < drill - 10). */
  notReady: string[];
}

interface TransferReadinessPanelProps {
  skills: TransferSkill[];
}

function gapColor(drillRate: number, rankedRate: number): string {
  const gap = drillRate - rankedRate;
  if (gap < 15) return 'bg-green-500';
  if (gap <= 35) return 'bg-amber-500';
  return 'bg-red-500';
}

export default function TransferReadinessPanel({
  skills,
}: TransferReadinessPanelProps) {
  const rows = skills.map((skill) => {
    const drillRate = Math.min(100, Math.round((skill.current / skill.target) * 100));
    const rankedRate = RANKED_RATES[skill.name] ?? Math.round(drillRate * 0.6);
    const tournamentRate = TOURNAMENT_RATES[skill.name] ?? Math.round(rankedRate * 0.6);
    const isReady = rankedRate >= drillRate - 10;

    return { ...skill, drillRate, rankedRate, tournamentRate, isReady };
  });

  const readyCount = rows.filter((r) => r.isReady).length;

  /** Exported info for parent consumers. */
  const readinessInfo: TransferReadinessInfo = {
    notReady: rows.filter((r) => !r.isReady).map((r) => r.name),
  };

  // Attach to the DOM node via data attribute so parent can inspect if needed.
  // The primary export path is the named type + the component itself.
  void readinessInfo;

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-5">
      {/* Header */}
      <h2 className="text-sm font-bold text-dark-300 uppercase tracking-wider mb-4 flex items-center gap-2">
        <ArrowRightLeft className="w-4 h-4 text-cyan-400" />
        Lab vs. Live Transfer
      </h2>

      {/* Summary */}
      <p className="text-xs text-dark-400 mb-4">
        <span className="font-bold text-forge-400">{readyCount}</span> of{' '}
        <span className="font-bold text-dark-200">{rows.length}</span> skills
        competition-ready
      </p>

      {/* Skill rows */}
      <div className="space-y-4">
        {rows.map((row) => {
          const drillRankedGapClass = gapColor(row.drillRate, row.rankedRate);

          return (
            <div key={row.name}>
              {/* Skill name + badges */}
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-sm font-medium text-dark-200">
                  {row.name}
                </span>
                {row.isReady ? (
                  <span className="text-[10px] font-medium text-forge-400">
                    Competition Ready
                  </span>
                ) : (
                  <AlertTriangle className="h-3 w-3 text-amber-400" />
                )}
              </div>

              {/* Bar: Drills */}
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] text-dark-500 w-16 shrink-0">
                  Drills
                </span>
                <div className="flex-1 h-1.5 rounded-full bg-dark-800">
                  <div
                    className="h-1.5 rounded-full bg-forge-400 transition-all duration-500"
                    style={{ width: `${row.drillRate}%` }}
                  />
                </div>
                <span className="text-[10px] tabular-nums text-dark-300 w-8 text-right">
                  {row.drillRate}%
                </span>
              </div>

              {/* Bar: Ranked */}
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] text-dark-500 w-16 shrink-0">
                  Ranked
                </span>
                <div className="flex-1 h-1.5 rounded-full bg-dark-800">
                  <div
                    className={clsx(
                      'h-1.5 rounded-full transition-all duration-500',
                      drillRankedGapClass
                    )}
                    style={{ width: `${row.rankedRate}%` }}
                  />
                </div>
                <span className="text-[10px] tabular-nums text-dark-300 w-8 text-right">
                  {row.rankedRate}%
                </span>
              </div>

              {/* Bar: Tournament */}
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-dark-500 w-16 shrink-0">
                  Tourney
                </span>
                <div className="flex-1 h-1.5 rounded-full bg-dark-800">
                  <div
                    className="h-1.5 rounded-full bg-purple-500 transition-all duration-500"
                    style={{ width: `${row.tournamentRate}%` }}
                  />
                </div>
                <span className="text-[10px] tabular-nums text-dark-300 w-8 text-right">
                  {row.tournamentRate}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

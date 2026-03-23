'use client';

import { Target, AlertTriangle, Check } from 'lucide-react';

interface PriorityFix {
  name: string;
  fixedDate: string;
  winRateBefore: number;
  winRateAfter: number;
  delta: number;
  improved: boolean;
}

const mockFixes: PriorityFix[] = [
  { name: 'Coverage Read Speed', fixedDate: 'Mar 10', winRateBefore: 58, winRateAfter: 62.2, delta: 4.2, improved: true },
  { name: 'Red Zone Offense', fixedDate: 'Mar 5', winRateBefore: 55, winRateAfter: 58.1, delta: 3.1, improved: true },
  { name: 'Blitz Recognition', fixedDate: 'Feb 28', winRateBefore: 52, winRateAfter: 52.3, delta: 0.3, improved: false },
  { name: 'Clock Management', fixedDate: 'Feb 20', winRateBefore: 49, winRateAfter: 54.8, delta: 5.8, improved: true },
];

export default function ImpactRankROI() {
  const improvedCount = mockFixes.filter((f) => f.improved).length;
  const total = mockFixes.length;
  const roiPercent = Math.round((improvedCount / total) * 100);

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="flex items-center gap-3 mb-5">
        <Target className="w-5 h-5 text-forge-400" />
        <div>
          <h2 className="text-lg font-bold text-dark-100">ImpactRank ROI</h2>
          <p className="text-sm text-dark-400">Did fixing priorities work?</p>
        </div>
      </div>

      <div className="space-y-3">
        {mockFixes.map((fix) => {
          const maxRate = Math.max(fix.winRateBefore, fix.winRateAfter, 70);
          const beforeWidth = (fix.winRateBefore / maxRate) * 100;
          const afterWidth = (fix.winRateAfter / maxRate) * 100;

          return (
            <div
              key={fix.name}
              className="p-4 rounded-lg bg-dark-800/50 border border-dark-700"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-dark-100">
                  {fix.name} fixed ({fix.fixedDate}) &rarr; Win Rate{' '}
                  {fix.delta >= 2 ? '+' : ''}
                  {fix.delta}%
                </span>
                {fix.improved ? (
                  <Check className="w-4 h-4 text-forge-400" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                )}
              </div>

              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs text-dark-500 w-14 text-right">
                  {fix.winRateBefore}%
                </span>
                <div className="flex-1 h-2.5 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-dark-600 rounded-full transition-all duration-500"
                    style={{ width: `${beforeWidth}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-dark-500 w-14 text-right">
                  {fix.winRateAfter}%
                </span>
                <div className="flex-1 h-2.5 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-forge-500 rounded-full transition-all duration-500"
                    style={{ width: `${afterWidth}%` }}
                  />
                </div>
              </div>

              {!fix.improved && (
                <div className="flex items-center gap-2 mt-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-xs text-amber-400">
                    Unexpected: win rate flat — Truth Engine investigating
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-5 pt-4 border-t border-dark-700">
        <p className="text-sm text-dark-300">
          ImpactRank accuracy:{' '}
          <span className="font-bold text-dark-100">
            {improvedCount} of {total}
          </span>{' '}
          fixes improved win rate —{' '}
          <span className="font-bold text-forge-400">{roiPercent}% recommendation ROI</span>
        </p>
      </div>
    </div>
  );
}

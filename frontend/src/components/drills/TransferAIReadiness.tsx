'use client';

import { ArrowRightLeft, AlertTriangle } from 'lucide-react';

interface TransferMetric {
  skill: string;
  labScore: number;
  liveScore: number;
}

const MOCK_METRICS: TransferMetric[] = [
  { skill: 'Coverage Reads', labScore: 85, liveScore: 62 },
  { skill: 'Blitz Recognition', labScore: 78, liveScore: 54 },
  { skill: 'Red Zone Execution', labScore: 91, liveScore: 71 },
  { skill: 'Route Combos', labScore: 72, liveScore: 58 },
  { skill: 'Audible Usage', labScore: 68, liveScore: 41 },
];

function gapColor(gap: number): string {
  if (gap <= 10) return 'text-forge-400';
  if (gap <= 20) return 'text-amber-400';
  return 'text-red-400';
}

function gapBarColor(gap: number): string {
  if (gap <= 10) return 'bg-forge-500';
  if (gap <= 20) return 'bg-amber-500';
  return 'bg-red-500';
}

/**
 * TransferAI Readiness panel for drills.
 * Shows "Lab: 85% -> Live: 62% -> Gap: 23pts" with visual bars per skill.
 */
export default function TransferAIReadiness() {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-5">
      <div className="flex items-center gap-2 mb-4">
        <ArrowRightLeft className="h-4 w-4 text-cyan-400" />
        <h2 className="text-sm font-bold text-dark-300 uppercase tracking-wider">
          TransferAI Readiness
        </h2>
      </div>

      <div className="space-y-4">
        {MOCK_METRICS.map((metric) => {
          const gap = metric.labScore - metric.liveScore;

          return (
            <div key={metric.skill}>
              {/* Skill name + gap badge */}
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-dark-200">{metric.skill}</span>
                <div className="flex items-center gap-1.5">
                  {gap > 20 && <AlertTriangle className="h-3 w-3 text-red-400" />}
                  <span className={`text-xs font-bold font-mono ${gapColor(gap)}`}>
                    Gap: {gap}pts
                  </span>
                </div>
              </div>

              {/* Score labels */}
              <div className="flex items-center gap-3 text-xs text-dark-400 mb-1">
                <span>
                  Lab: <span className="font-mono text-dark-200">{metric.labScore}%</span>
                </span>
                <span className="text-dark-600">&#8594;</span>
                <span>
                  Live: <span className="font-mono text-dark-200">{metric.liveScore}%</span>
                </span>
              </div>

              {/* Dual bars */}
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-dark-500 w-8 shrink-0">Lab</span>
                  <div className="flex-1 h-2 rounded-full bg-dark-800">
                    <div
                      className="h-2 rounded-full bg-forge-400/70 transition-all duration-500"
                      style={{ width: `${metric.labScore}%` }}
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-dark-500 w-8 shrink-0">Live</span>
                  <div className="flex-1 h-2 rounded-full bg-dark-800">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${gapBarColor(gap)}`}
                      style={{ width: `${metric.liveScore}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="mt-4 pt-3 border-t border-dark-700">
        <p className="text-xs text-dark-400">
          Largest gap:{' '}
          <span className="font-bold text-red-400">
            Audible Usage (-27pts)
          </span>{' '}
          — prioritize live reps
        </p>
      </div>
    </div>
  );
}

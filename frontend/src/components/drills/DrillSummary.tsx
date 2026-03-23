'use client';

import { DrillRecord } from '@/types/analytics';
import { DrillSkillProgress } from '@/hooks/useDrills';
import {
  Trophy,
  Target,
  TrendingUp,
  RotateCcw,
  CheckCircle2,
  XCircle,
  BarChart3,
} from 'lucide-react';

interface DrillSummaryProps {
  completedDrills: DrillRecord[];
  totalReps: number;
  overallSuccessRate: number;
  skillProgress: DrillSkillProgress[];
  onReset: () => void;
}

export default function DrillSummary({
  completedDrills,
  totalReps,
  overallSuccessRate,
  skillProgress,
  onReset,
}: DrillSummaryProps) {
  const avgImpactRank =
    completedDrills.length > 0
      ? (
          completedDrills.reduce((sum, d) => sum + d.impactRank, 0) /
          completedDrills.length
        ).toFixed(1)
      : '0';

  const totalImprovement = skillProgress.reduce(
    (sum, sp) => sum + (sp.current - sp.baseline),
    0
  );

  return (
    <div className="rounded-xl border border-forge-500/30 bg-gradient-to-b from-forge-950/20 to-dark-900/80 p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-forge-500/10 border border-forge-800/30">
          <Trophy className="w-6 h-6 text-forge-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-dark-50">Session Complete</h2>
          <p className="text-sm text-dark-400">Here is your drill summary</p>
        </div>
      </div>

      {/* Top Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="rounded-lg border border-dark-700 bg-dark-800/50 p-4 text-center">
          <BarChart3 className="w-5 h-5 text-forge-400 mx-auto mb-1" />
          <p className="text-2xl font-bold font-mono text-dark-50">
            {totalReps}
          </p>
          <p className="text-[10px] text-dark-500 uppercase tracking-wider">
            Total Reps
          </p>
        </div>
        <div className="rounded-lg border border-dark-700 bg-dark-800/50 p-4 text-center">
          <CheckCircle2 className="w-5 h-5 text-forge-400 mx-auto mb-1" />
          <p className="text-2xl font-bold font-mono text-dark-50">
            {overallSuccessRate}%
          </p>
          <p className="text-[10px] text-dark-500 uppercase tracking-wider">
            Success Rate
          </p>
        </div>
        <div className="rounded-lg border border-dark-700 bg-dark-800/50 p-4 text-center">
          <Target className="w-5 h-5 text-cyan-400 mx-auto mb-1" />
          <p className="text-2xl font-bold font-mono text-dark-50">
            {completedDrills.length}
          </p>
          <p className="text-[10px] text-dark-500 uppercase tracking-wider">
            Drills Done
          </p>
        </div>
        <div className="rounded-lg border border-dark-700 bg-dark-800/50 p-4 text-center">
          <TrendingUp className="w-5 h-5 text-purple-400 mx-auto mb-1" />
          <p className="text-2xl font-bold font-mono text-dark-50">
            {avgImpactRank}
          </p>
          <p className="text-[10px] text-dark-500 uppercase tracking-wider">
            Avg Impact Rank
          </p>
        </div>
      </div>

      {/* Drill Breakdown */}
      <div className="mb-6">
        <h3 className="text-sm font-bold text-dark-300 uppercase tracking-wider mb-3">
          Drill Breakdown
        </h3>
        <div className="space-y-2">
          {completedDrills.map((drill) => (
            <div
              key={drill.id}
              className="flex items-center justify-between p-3 rounded-lg bg-dark-800/40 border border-dark-700/50"
            >
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-dark-200">
                  {drill.name}
                </span>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-dark-400 font-mono">
                  {drill.completedReps}/{drill.reps} reps
                </span>
                <span
                  className={`font-mono font-bold ${
                    drill.successRate >= 70
                      ? 'text-forge-400'
                      : drill.successRate >= 50
                      ? 'text-yellow-400'
                      : 'text-red-400'
                  }`}
                >
                  {drill.successRate}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Improvement Trend */}
      <div className="mb-6">
        <h3 className="text-sm font-bold text-dark-300 uppercase tracking-wider mb-3">
          Improvement Trend
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {skillProgress.map((sp) => {
            const gain = sp.current - sp.baseline;
            return (
              <div
                key={sp.name}
                className="p-3 rounded-lg bg-dark-800/40 border border-dark-700/50"
              >
                <p className="text-xs text-dark-400 mb-1">{sp.name}</p>
                <div className="flex items-end gap-1.5">
                  <span className="text-lg font-bold font-mono text-dark-100">
                    {Math.round(sp.current)}
                  </span>
                  {gain > 0 && (
                    <span className="text-xs text-forge-400 font-medium mb-0.5">
                      +{gain.toFixed(1)}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-5 py-2.5 bg-forge-500 hover:bg-forge-600 text-dark-950 font-bold rounded-lg transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          New Session
        </button>
      </div>
    </div>
  );
}

'use client';

import { DrillRecord } from '@/types/analytics';
import {
  Play,
  CheckCircle2,
  SkipForward,
  Flame,
  Target,
  Gauge,
  Sparkles,
} from 'lucide-react';

interface DrillRunnerProps {
  drill: DrillRecord;
  onCompleteRep: () => void;
  onSkip: () => void;
  onStart: () => void;
  isActive: boolean;
}

const difficultyConfig: Record<
  string,
  { color: string; label: string; dots: number }
> = {
  beginner: { color: 'text-green-400', label: 'Beginner', dots: 1 },
  intermediate: { color: 'text-yellow-400', label: 'Intermediate', dots: 2 },
  advanced: { color: 'text-orange-400', label: 'Advanced', dots: 3 },
  elite: { color: 'text-red-400', label: 'Elite', dots: 4 },
};

export default function DrillRunner({
  drill,
  onCompleteRep,
  onSkip,
  onStart,
  isActive,
}: DrillRunnerProps) {
  const progress = drill.reps > 0 ? (drill.completedReps / drill.reps) * 100 : 0;
  const diffConfig = difficultyConfig[drill.difficulty];

  return (
    <div
      className={`rounded-xl border p-6 transition-all duration-300 ${
        isActive
          ? 'border-forge-500/50 bg-gradient-to-b from-forge-950/30 to-dark-900/80 shadow-lg shadow-forge-500/5'
          : 'border-dark-700 bg-dark-900/50'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-dark-50">{drill.name}</h2>
            {drill.isDynamicCalibration && (
              <span className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold uppercase bg-purple-500/20 text-purple-400 border border-purple-800/30 rounded">
                <Sparkles className="w-3 h-3" />
                Dynamic Calibration
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-1">
            <div className="flex items-center gap-1">
              <Gauge className={`w-4 h-4 ${diffConfig.color}`} />
              <span className={`text-sm font-medium ${diffConfig.color}`}>
                {diffConfig.label}
              </span>
            </div>
            <span className="text-dark-600">|</span>
            <div className="flex items-center gap-1">
              <Flame className="w-4 h-4 text-orange-400" />
              <span className="text-sm text-dark-400">
                IR: <span className="font-mono font-bold text-dark-200">{drill.impactRank}</span>
              </span>
            </div>
          </div>
        </div>

        {/* Success Rate */}
        <div className="text-right">
          <p className="text-2xl font-bold font-mono text-forge-400">{drill.successRate}%</p>
          <p className="text-[10px] text-dark-500 uppercase tracking-wider">Success Rate</p>
        </div>
      </div>

      {/* Instructions */}
      <div className="p-4 rounded-lg bg-dark-800/60 border border-dark-700 mb-4">
        <p className="text-sm text-dark-200 leading-relaxed">{drill.instructions}</p>
      </div>

      {/* Progress */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-dark-400">
            Reps: <span className="font-mono text-dark-200">{drill.completedReps}/{drill.reps}</span>
          </span>
          <span className="text-sm font-mono text-dark-400">{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-dark-800 rounded-full h-3">
          <div
            className="h-3 rounded-full bg-gradient-to-r from-forge-600 to-forge-400 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Skill Targets */}
      {drill.skillTargets.length > 0 && (
        <div className="mb-5">
          <h3 className="text-sm font-medium text-dark-300 mb-2 flex items-center gap-1.5">
            <Target className="w-4 h-4" />
            Skill Targets
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {drill.skillTargets.map((target) => (
              <div key={target.name} className="flex items-center gap-2">
                <span className="text-xs text-dark-400 w-24 truncate">{target.name}</span>
                <div className="flex-1 bg-dark-800 rounded-full h-1.5">
                  <div
                    className="h-1.5 rounded-full bg-cyan-500"
                    style={{ width: `${(target.current / target.target) * 100}%` }}
                  />
                </div>
                <span className="text-[10px] font-mono text-dark-500">
                  {target.current}/{target.target}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center gap-3">
        {!isActive ? (
          <button
            onClick={onStart}
            className="flex items-center gap-2 px-5 py-2.5 bg-forge-500 hover:bg-forge-600 text-dark-950 font-bold rounded-lg transition-colors"
          >
            <Play className="w-4 h-4" />
            Start Drill
          </button>
        ) : (
          <>
            <button
              onClick={onCompleteRep}
              className="flex items-center gap-2 px-5 py-2.5 bg-forge-500 hover:bg-forge-600 text-dark-950 font-bold rounded-lg transition-colors"
            >
              <CheckCircle2 className="w-4 h-4" />
              Complete Rep
            </button>
            <button
              onClick={onSkip}
              className="flex items-center gap-2 px-4 py-2.5 bg-dark-800 hover:bg-dark-700 text-dark-300 font-medium rounded-lg border border-dark-600 transition-colors"
            >
              <SkipForward className="w-4 h-4" />
              Skip
            </button>
          </>
        )}
      </div>
    </div>
  );
}

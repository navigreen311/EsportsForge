'use client';

import { Target, TrendingUp } from 'lucide-react';
import { DrillSkillProgress } from '@/hooks/useDrills';

interface SkillProgressProps {
  skills: DrillSkillProgress[];
}

export default function SkillProgress({ skills }: SkillProgressProps) {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-5">
      <h2 className="text-sm font-bold text-dark-300 uppercase tracking-wider mb-4 flex items-center gap-2">
        <Target className="w-4 h-4 text-cyan-400" />
        Skill Progress
      </h2>

      <div className="space-y-4">
        {skills.map((skill) => {
          const progressPercent = Math.min(
            100,
            (skill.current / skill.target) * 100
          );
          const gain = skill.current - skill.baseline;
          const isOnTrack = progressPercent >= 70;

          return (
            <div key={skill.name}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-dark-200">
                  {skill.name}
                </span>
                <div className="flex items-center gap-2">
                  {gain > 0 && (
                    <span className="flex items-center gap-0.5 text-[10px] text-forge-400">
                      <TrendingUp className="w-3 h-3" />+
                      {gain.toFixed(1)}
                    </span>
                  )}
                  <span className="text-xs font-mono text-dark-400">
                    {Math.round(skill.current)}/{skill.target}
                  </span>
                </div>
              </div>

              {/* Progress bar */}
              <div className="relative w-full bg-dark-800 rounded-full h-2.5">
                {/* Target marker */}
                <div
                  className="absolute top-0 h-2.5 w-px bg-dark-500"
                  style={{ left: '100%' }}
                  title={`Target: ${skill.target}`}
                />
                {/* Current progress */}
                <div
                  className={`h-2.5 rounded-full transition-all duration-500 ${
                    isOnTrack
                      ? 'bg-gradient-to-r from-forge-600 to-forge-400'
                      : 'bg-gradient-to-r from-yellow-600 to-yellow-400'
                  }`}
                  style={{ width: `${progressPercent}%` }}
                />
              </div>

              {/* Baseline marker label */}
              <div className="flex justify-between mt-0.5">
                <span className="text-[9px] text-dark-600">
                  Baseline: {skill.baseline}
                </span>
                <span
                  className={`text-[9px] font-medium ${
                    isOnTrack ? 'text-forge-500' : 'text-yellow-500'
                  }`}
                >
                  {Math.round(progressPercent)}% to target
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

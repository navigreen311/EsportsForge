'use client';

import { ExecutionCeilingSkill } from '@/hooks/useProfile';
import { Zap } from 'lucide-react';

interface ExecutionCeilingProps {
  skills: ExecutionCeilingSkill[];
}

export default function ExecutionCeiling({ skills }: ExecutionCeilingProps) {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <h2 className="text-lg font-bold text-dark-100 mb-1 flex items-center gap-2">
        <Zap className="w-5 h-5 text-yellow-400" />
        Execution Ceiling
      </h2>
      <p className="text-xs text-dark-500 mb-4">
        Normal vs under-pressure performance
      </p>

      <div className="space-y-4">
        {skills.map((skill) => {
          const drop = skill.normal - skill.pressure;
          return (
            <div key={skill.name}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-dark-200">
                  {skill.name}
                </span>
                <span
                  className={`text-[10px] font-mono font-bold ${
                    drop > 15
                      ? 'text-red-400'
                      : drop > 8
                      ? 'text-yellow-400'
                      : 'text-forge-400'
                  }`}
                >
                  -{drop} under pressure
                </span>
              </div>

              {/* Dual bars */}
              <div className="space-y-1">
                {/* Normal */}
                <div className="flex items-center gap-2">
                  <span className="text-[9px] text-dark-500 w-14">Normal</span>
                  <div className="flex-1 bg-dark-800 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-forge-600 to-forge-400"
                      style={{ width: `${skill.normal}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-mono text-dark-400 w-8 text-right">
                    {skill.normal}
                  </span>
                </div>
                {/* Pressure */}
                <div className="flex items-center gap-2">
                  <span className="text-[9px] text-dark-500 w-14">
                    Pressure
                  </span>
                  <div className="flex-1 bg-dark-800 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        drop > 15
                          ? 'bg-gradient-to-r from-red-600 to-red-400'
                          : drop > 8
                          ? 'bg-gradient-to-r from-yellow-600 to-yellow-400'
                          : 'bg-gradient-to-r from-forge-600 to-forge-400'
                      }`}
                      style={{ width: `${skill.pressure}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-mono text-dark-400 w-8 text-right">
                    {skill.pressure}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

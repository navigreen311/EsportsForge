'use client';

import { Encounter } from '@/types/opponent';
import { Trophy, Swords, GraduationCap } from 'lucide-react';

interface EncounterHistoryProps {
  encounters: Encounter[];
}

const modeIcons: Record<string, React.ReactNode> = {
  ranked: <Trophy className="w-3.5 h-3.5 text-yellow-400" />,
  tournament: <Swords className="w-3.5 h-3.5 text-red-400" />,
  training: <GraduationCap className="w-3.5 h-3.5 text-blue-400" />,
};

const modeColors: Record<string, string> = {
  ranked: 'bg-yellow-500/10 text-yellow-400 border-yellow-800/50',
  tournament: 'bg-red-500/10 text-red-400 border-red-800/50',
  training: 'bg-blue-500/10 text-blue-400 border-blue-800/50',
};

export default function EncounterHistory({ encounters }: EncounterHistoryProps) {
  if (encounters.length === 0) {
    return (
      <div className="text-center py-12 text-dark-500">
        No encounters recorded yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {encounters.map((enc) => (
        <div
          key={enc.id}
          className="flex items-start gap-4 p-4 rounded-lg bg-dark-800/50 border border-dark-700 hover:border-dark-600 transition-colors"
        >
          {/* Result indicator */}
          <div
            className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold uppercase ${
              enc.result === 'win'
                ? 'bg-forge-500/15 text-forge-400 border border-forge-800/30'
                : 'bg-red-500/15 text-red-400 border border-red-800/30'
            }`}
          >
            {enc.result === 'win' ? 'W' : 'L'}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              <span className="text-sm font-bold font-mono text-dark-100">
                {enc.score}
              </span>
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium border ${modeColors[enc.mode]}`}
              >
                {modeIcons[enc.mode]}
                {enc.mode}
              </span>
            </div>
            <p className="text-xs text-dark-400 mt-1">{enc.notes}</p>
          </div>

          <div className="flex-shrink-0 text-right">
            <span className="text-xs text-dark-500">{enc.date}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

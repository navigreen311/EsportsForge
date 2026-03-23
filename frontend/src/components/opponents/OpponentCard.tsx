'use client';

import { Opponent } from '@/types/opponent';
import { Swords, Eye, Trophy, Clock, Star } from 'lucide-react';

interface OpponentCardProps {
  opponent: Opponent;
  onClick: (opponent: Opponent) => void;
}

const archetypeColors: Record<string, string> = {
  'Aggressive Rusher': 'bg-red-500/20 text-red-400 border-red-800/50',
  'Pocket Passer': 'bg-blue-500/20 text-blue-400 border-blue-800/50',
  'Scrambler': 'bg-orange-500/20 text-orange-400 border-orange-800/50',
  'Zone Specialist': 'bg-cyan-500/20 text-cyan-400 border-cyan-800/50',
  'Blitz Heavy': 'bg-purple-500/20 text-purple-400 border-purple-800/50',
  'Run First': 'bg-green-500/20 text-green-400 border-green-800/50',
  'Balanced': 'bg-dark-600/50 text-dark-300 border-dark-500/50',
  'West Coast': 'bg-teal-500/20 text-teal-400 border-teal-800/50',
  'Air Raid': 'bg-yellow-500/20 text-yellow-400 border-yellow-800/50',
  'Defensive Mastermind': 'bg-indigo-500/20 text-indigo-400 border-indigo-800/50',
};

function getRivalDepth(encounterCount: number): string | null {
  if (encounterCount >= 8) return 'Nemesis';
  if (encounterCount >= 5) return 'Arch-Rival';
  if (encounterCount >= 2) return 'Rival';
  return null;
}

export default function OpponentCard({ opponent, onClick }: OpponentCardProps) {
  const winRateColor =
    opponent.winRate >= 60
      ? 'text-forge-400'
      : opponent.winRate >= 40
        ? 'text-yellow-400'
        : 'text-red-400';

  const rivalDepth = opponent.isRival ? getRivalDepth(opponent.encounterCount) : null;

  return (
    <button
      onClick={() => onClick(opponent)}
      className="w-full text-left rounded-xl border border-dark-700 bg-dark-900/50 p-5 hover:border-dark-500 hover:bg-dark-900/80 transition-all duration-200 group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-full bg-dark-800 border border-dark-600 flex items-center justify-center text-lg font-bold text-dark-300 group-hover:border-dark-500">
            {opponent.gamertag.charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-dark-100">{opponent.gamertag}</h3>
              {opponent.isRival && (
                <div className="flex items-center gap-1" title={rivalDepth ?? 'Rival'}>
                  <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                  {rivalDepth && (
                    <span className="text-[10px] font-medium text-yellow-400/80">
                      {rivalDepth}
                    </span>
                  )}
                </div>
              )}
            </div>
            <span
              className={`inline-block mt-1 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider rounded border ${
                archetypeColors[opponent.archetype] || 'bg-dark-700 text-dark-300 border-dark-600'
              }`}
            >
              {opponent.archetype}
            </span>
          </div>
        </div>
        <div className={`text-xl font-bold font-mono ${winRateColor}`}>
          {opponent.winRate}%
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-dark-800">
        <div className="flex items-center gap-1.5 text-dark-400">
          <Trophy className="w-3.5 h-3.5" />
          <span className="text-xs">{opponent.encounterCount} games</span>
        </div>
        <div className="flex items-center gap-1.5 text-dark-400">
          <Eye className="w-3.5 h-3.5" />
          <span className="text-xs">
            {opponent.weaknesses.filter((w) => w.severity === 'critical' || w.severity === 'high').length} weak pts
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-dark-400">
          <Clock className="w-3.5 h-3.5" />
          <span className="text-xs">{opponent.lastSeen}</span>
        </div>
      </div>
    </button>
  );
}

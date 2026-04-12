'use client';

import { Trophy, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface GameState {
  label: string;
  winRate: number;
  gamesPlayed: number;
  trend: 'up' | 'down' | 'stable';
  color: string;
  bgColor: string;
  borderColor: string;
}

const GAME_STATES: GameState[] = [
  {
    label: 'Ahead 7+',
    winRate: 89,
    gamesPlayed: 18,
    trend: 'stable',
    color: 'text-forge-400',
    bgColor: 'bg-forge-500/10',
    borderColor: 'border-forge-800/40',
  },
  {
    label: 'Within 7',
    winRate: 62,
    gamesPlayed: 31,
    trend: 'up',
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/10',
    borderColor: 'border-cyan-800/40',
  },
  {
    label: 'Tied',
    winRate: 55,
    gamesPlayed: 14,
    trend: 'up',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-800/40',
  },
  {
    label: 'Down 7',
    winRate: 38,
    gamesPlayed: 22,
    trend: 'down',
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-800/40',
  },
  {
    label: 'Down 14+',
    winRate: 12,
    gamesPlayed: 9,
    trend: 'down',
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-800/40',
  },
  {
    label: 'Overtime',
    winRate: 67,
    gamesPlayed: 6,
    trend: 'up',
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-800/40',
  },
];

function TrendIcon({ trend }: { trend: GameState['trend'] }) {
  switch (trend) {
    case 'up':
      return <TrendingUp className="h-4 w-4 text-forge-400" />;
    case 'down':
      return <TrendingDown className="h-4 w-4 text-red-400" />;
    case 'stable':
      return <Minus className="h-4 w-4 text-dark-400" />;
  }
}

/**
 * Win conditions panel showing win rates across 6 game states:
 * Ahead 7+, Within 7, Tied, Down 7, Down 14+, OT.
 */
export default function WinConditions() {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="mb-5 flex items-center gap-3">
        <Trophy className="h-5 w-5 text-forge-400" />
        <div>
          <h2 className="text-lg font-semibold text-white">Win Conditions</h2>
          <p className="text-sm text-dark-400">
            Win rate by game state
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        {GAME_STATES.map((state) => (
          <div
            key={state.label}
            className={`rounded-lg border p-4 transition-colors ${state.bgColor} ${state.borderColor}`}
          >
            <p className={`text-sm font-medium ${state.color}`}>{state.label}</p>

            <div className="mt-2 flex items-center justify-between">
              <span
                className={`font-mono text-2xl font-bold ${state.color}`}
              >
                {state.winRate}%
              </span>
              <TrendIcon trend={state.trend} />
            </div>

            {/* Mini progress bar */}
            <div className="mt-2 h-1.5 w-full rounded-full bg-dark-700/50">
              <div
                className={`h-1.5 rounded-full transition-all duration-500 ${
                  state.winRate >= 60
                    ? 'bg-forge-500'
                    : state.winRate >= 40
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                }`}
                style={{ width: `${state.winRate}%` }}
              />
            </div>

            <p className="mt-1 text-[10px] text-dark-500">
              {state.gamesPlayed} game{state.gamesPlayed !== 1 ? 's' : ''}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

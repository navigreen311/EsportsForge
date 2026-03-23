'use client';

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { clsx } from 'clsx';

interface WinRateTrendProps {
  winRate: number;
  opponentId: string;
}

type TrendDirection = 'up' | 'down' | 'stable';

const WIN_RATE_HISTORY: Record<string, ('W' | 'L')[]> = {
  'opp-1': ['W', 'W', 'L', 'W', 'W'],
  'opp-2': ['L', 'L', 'W', 'L', 'W'],
  'opp-3': ['W', 'L', 'W', 'W', 'L'],
  'opp-4': ['W', 'W', 'W', 'L', 'W'],
  'opp-5': ['L', 'W', 'L', 'L', 'L'],
  'opp-6': ['W', 'L', 'W', 'L', 'W'],
};

function calculateTrend(history: ('W' | 'L')[]): TrendDirection {
  const first2Wins = history.slice(0, 2).filter((r) => r === 'W').length;
  const last3Wins = history.slice(2).filter((r) => r === 'W').length;
  const first2Losses = 2 - first2Wins;
  const last3Losses = 3 - last3Wins;

  if (last3Wins > first2Wins) return 'up';
  if (last3Losses > first2Losses) return 'down';
  return 'stable';
}

const trendTextColor: Record<TrendDirection, string> = {
  up: 'text-forge-400',
  down: 'text-red-400',
  stable: 'text-dark-300',
};

const trendLabel: Record<TrendDirection, string> = {
  up: 'improving',
  down: 'declining',
  stable: 'stable',
};

export default function WinRateTrend({ winRate, opponentId }: WinRateTrendProps) {
  const history = WIN_RATE_HISTORY[opponentId] ?? ['L', 'L', 'L', 'L', 'L'];
  const trend = calculateTrend(history);
  const last3 = history.slice(2);
  const tooltip = `Last 3 games: ${last3.join(' ')} — ${trendLabel[trend]}`;

  return (
    <span
      className="inline-flex items-center gap-2"
      title={tooltip}
    >
      <span
        className={clsx(
          'text-xl font-bold font-mono',
          trendTextColor[trend],
        )}
      >
        {winRate}%
      </span>

      {trend === 'up' && (
        <TrendingUp className="h-4 w-4 text-forge-400" />
      )}
      {trend === 'down' && (
        <TrendingDown className="h-4 w-4 text-red-400" />
      )}
      {trend === 'stable' && (
        <Minus className="h-4 w-4 text-dark-400" />
      )}

      <span className="inline-flex items-center gap-0.5">
        {history.map((result, i) => (
          <span
            key={i}
            className={clsx(
              'h-1.5 w-1.5 rounded-full',
              result === 'W' ? 'bg-forge-400' : 'bg-red-400',
            )}
          />
        ))}
      </span>
    </span>
  );
}

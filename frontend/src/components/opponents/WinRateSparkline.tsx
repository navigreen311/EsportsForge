'use client';

import { TrendingUp, TrendingDown } from 'lucide-react';

interface WinRateSparklineProps {
  opponentId: string;
}

/** Mock last-10-game results per opponent. */
const GAME_HISTORY: Record<string, ('W' | 'L')[]> = {
  'opp-1': ['L', 'W', 'L', 'W', 'W', 'W', 'L', 'W', 'W', 'W'],
  'opp-2': ['W', 'L', 'L', 'W', 'L', 'L', 'W', 'L', 'L', 'W'],
  'opp-3': ['W', 'W', 'L', 'W', 'L', 'W', 'W', 'L', 'W', 'L'],
  'opp-4': ['W', 'W', 'W', 'L', 'W', 'W', 'W', 'L', 'W', 'W'],
  'opp-5': ['L', 'L', 'W', 'L', 'L', 'L', 'W', 'L', 'L', 'L'],
  'opp-6': ['W', 'L', 'W', 'L', 'W', 'L', 'W', 'L', 'W', 'W'],
};

/**
 * Sparkline of last 10 games vs an opponent.
 * Green dots for wins, red for losses, with a trend arrow.
 */
export default function WinRateSparkline({ opponentId }: WinRateSparklineProps) {
  const history = GAME_HISTORY[opponentId] ?? [];
  if (history.length === 0) return null;

  // Calculate rolling win rates for sparkline points
  const points = history.map((_, i) => {
    const slice = history.slice(0, i + 1);
    const wins = slice.filter((r) => r === 'W').length;
    return Math.round((wins / slice.length) * 100);
  });

  // Determine overall trend from first half vs second half
  const firstHalf = history.slice(0, 5).filter((r) => r === 'W').length;
  const secondHalf = history.slice(5).filter((r) => r === 'W').length;
  const trending = secondHalf > firstHalf ? 'up' : secondHalf < firstHalf ? 'down' : 'stable';
  const currentWinRate = points[points.length - 1];

  // SVG sparkline
  const width = 80;
  const height = 24;
  const padding = 2;
  const plotWidth = width - padding * 2;
  const plotHeight = height - padding * 2;

  const svgPoints = points.map((val, i) => {
    const x = padding + (i / (points.length - 1)) * plotWidth;
    const y = padding + plotHeight - (val / 100) * plotHeight;
    return `${x},${y}`;
  });

  const lineColor = trending === 'up' ? '#4ade80' : trending === 'down' ? '#f87171' : '#94a3b8';

  return (
    <div className="flex items-center gap-2">
      {/* SVG sparkline */}
      <svg width={width} height={height} className="shrink-0">
        <polyline
          fill="none"
          stroke={lineColor}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={svgPoints.join(' ')}
        />
        {/* Dots for each game */}
        {points.map((val, i) => {
          const x = padding + (i / (points.length - 1)) * plotWidth;
          const y = padding + plotHeight - (val / 100) * plotHeight;
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r="2"
              fill={history[i] === 'W' ? '#4ade80' : '#f87171'}
            />
          );
        })}
      </svg>

      {/* Trend indicator */}
      <div className="flex items-center gap-1">
        <span
          className={`text-xs font-mono font-bold ${
            trending === 'up'
              ? 'text-forge-400'
              : trending === 'down'
                ? 'text-red-400'
                : 'text-dark-400'
          }`}
        >
          {currentWinRate}%
        </span>
        {trending === 'up' && <TrendingUp className="h-3.5 w-3.5 text-forge-400" />}
        {trending === 'down' && <TrendingDown className="h-3.5 w-3.5 text-red-400" />}
      </div>
    </div>
  );
}

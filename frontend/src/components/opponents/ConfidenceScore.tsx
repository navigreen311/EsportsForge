'use client';

import { clsx } from 'clsx';

interface ConfidenceScoreProps {
  confidence: number;
  gamesObserved: number;
  className?: string;
}

type ConfidenceLevel = 'high' | 'medium' | 'low';

function getConfidenceLevel(confidence: number, gamesObserved: number): ConfidenceLevel {
  if (confidence >= 80 && gamesObserved >= 8) return 'high';
  if (confidence < 60 || gamesObserved < 4) return 'low';
  return 'medium';
}

const levelTextColor: Record<ConfidenceLevel, string> = {
  high: 'text-forge-400',
  medium: 'text-dark-300',
  low: 'text-amber-400',
};

const levelDotColor: Record<ConfidenceLevel, string> = {
  high: 'bg-forge-400',
  medium: 'bg-dark-400',
  low: 'bg-amber-400',
};

export default function ConfidenceScore({
  confidence,
  gamesObserved,
  className,
}: ConfidenceScoreProps) {
  const level = getConfidenceLevel(confidence, gamesObserved);

  return (
    <span
      className={clsx(
        'text-[10px] tabular-nums font-medium',
        levelTextColor[level],
        className,
      )}
      {...(level === 'low' && {
        title: 'Limited sample — tendency may not be reliable',
      })}
    >
      {level === 'low' && '*'}
      [{confidence}% conf, {gamesObserved} games]
    </span>
  );
}

export function ConfidenceIndicator({
  confidence,
  gamesObserved,
  className,
}: ConfidenceScoreProps) {
  const level = getConfidenceLevel(confidence, gamesObserved);

  return (
    <span
      className={clsx(
        'h-1 w-1 rounded-full inline-block',
        levelDotColor[level],
        className,
      )}
    />
  );
}

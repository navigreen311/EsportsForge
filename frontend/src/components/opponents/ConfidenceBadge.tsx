'use client';

import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react';
import clsx from 'clsx';

interface ConfidenceBadgeProps {
  gamesObserved: number;
  className?: string;
}

type ConfidenceTier = 'high' | 'medium' | 'low';

function getTier(games: number): ConfidenceTier {
  if (games >= 10) return 'high';
  if (games >= 5) return 'medium';
  return 'low';
}

const tierConfig: Record<
  ConfidenceTier,
  { label: string; bg: string; text: string; border: string; Icon: typeof Shield }
> = {
  high: {
    label: 'High confidence',
    bg: 'bg-forge-500/15',
    text: 'text-forge-400',
    border: 'border-forge-800/40',
    Icon: ShieldCheck,
  },
  medium: {
    label: 'Medium confidence',
    bg: 'bg-amber-500/15',
    text: 'text-amber-400',
    border: 'border-amber-800/40',
    Icon: Shield,
  },
  low: {
    label: 'Low confidence',
    bg: 'bg-red-500/15',
    text: 'text-red-400',
    border: 'border-red-800/40',
    Icon: ShieldAlert,
  },
};

/**
 * Badge showing data confidence level based on number of observed games.
 * E.g. "High confidence (47 games)" or "Low (3 games)".
 */
export default function ConfidenceBadge({
  gamesObserved,
  className,
}: ConfidenceBadgeProps) {
  const tier = getTier(gamesObserved);
  const config = tierConfig[tier];
  const { Icon } = config;

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium',
        config.bg,
        config.text,
        config.border,
        className,
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {config.label} ({gamesObserved} game{gamesObserved !== 1 ? 's' : ''})
    </span>
  );
}

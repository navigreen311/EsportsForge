/**
 * OpponentTendencyHeader — Top 3 tendencies as pills, archetype badge, win rate.
 * Compact header summary of opponent intel.
 */

'use client';

import { Eye } from 'lucide-react';
import { Badge } from '@/components/shared/Badge';

interface OpponentTendencyHeaderProps {
  opponentName: string;
}

interface TendencyPill {
  label: string;
  variant: 'info' | 'danger' | 'warning';
}

const topTendencies: TendencyPill[] = [
  { label: 'Cover 2: 68%', variant: 'info' },
  { label: 'Blitz-heavy: 34%', variant: 'danger' },
  { label: 'Run-first 3rd: 71%', variant: 'warning' },
];

const archetype = 'Defensive Schemer';
const winRateVs = 62;

export default function OpponentTendencyHeader({ opponentName }: OpponentTendencyHeaderProps) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-dark-700/50 bg-dark-900/60 px-4 py-2.5">
      {/* Label */}
      <div className="flex items-center gap-1.5 mr-2">
        <Eye className="h-3.5 w-3.5 text-dark-400" />
        <span className="text-xs font-medium text-dark-400">vs {opponentName}</span>
      </div>

      {/* Top 3 tendency pills */}
      {topTendencies.map((t, i) => (
        <Badge key={i} variant={t.variant} size="sm">
          {t.label}
        </Badge>
      ))}

      {/* Archetype badge */}
      <span className="rounded-full border border-purple-500/30 bg-purple-500/10 px-2.5 py-0.5 text-[10px] font-bold text-purple-400">
        {archetype}
      </span>

      {/* Win rate vs this opponent */}
      <span className="ml-auto rounded-md border border-forge-500/30 bg-forge-500/10 px-2 py-0.5 text-[11px] font-bold tabular-nums text-forge-400">
        Win Rate: {winRateVs}%
      </span>
    </div>
  );
}

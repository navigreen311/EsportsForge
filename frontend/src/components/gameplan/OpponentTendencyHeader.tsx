/**
 * OpponentTendencyHeader — Top tendencies as clickable filter pills,
 * archetype badge, win rate. Real data when GameplanAI has filled
 * `summary`; falls back to placeholder pills until then.
 */

'use client';

import { Eye, X } from 'lucide-react';
import { Badge } from '@/components/shared/Badge';
import type { OpponentSummary } from '@/types/gameplan';

interface OpponentTendencyHeaderProps {
  opponentName: string;
  summary?: OpponentSummary;
  archetype?: string | null;
  activeFilter?: string | null;
  onTagFilter?: (tag: string | null) => void;
}

function pillFromSummary(summary?: OpponentSummary): {
  label: string;
  variant: 'info' | 'danger' | 'warning';
  filter: string;
}[] {
  if (!summary) {
    return [
      { label: 'Cover 2: 68%', variant: 'info', filter: 'zone-beater' },
      { label: 'Blitz-heavy: 34%', variant: 'danger', filter: 'anti-blitz' },
      { label: 'Run-first 3rd: 71%', variant: 'warning', filter: 'run' },
    ];
  }
  const out: { label: string; variant: 'info' | 'danger' | 'warning'; filter: string }[] = [];
  if (summary.topCoverage) {
    out.push({
      label: `${summary.topCoverage}: ${summary.topCoveragePercent ?? '?'}%`,
      variant: 'info',
      filter: 'zone-beater',
    });
  }
  if (summary.blitzRate !== undefined) {
    out.push({
      label: `Blitz: ${summary.blitzRate}%`,
      variant: 'danger',
      filter: 'anti-blitz',
    });
  }
  if (summary.tendency3) {
    out.push({
      label: `${summary.tendency3}: ${summary.tendency3Percent ?? '?'}%`,
      variant: 'warning',
      filter: 'run',
    });
  }
  return out;
}

export default function OpponentTendencyHeader({
  opponentName,
  summary,
  archetype,
  activeFilter,
  onTagFilter,
}: OpponentTendencyHeaderProps) {
  const pills = pillFromSummary(summary);
  const archetypeLabel = archetype || summary?.defensiveSchemer || 'Unclassified';
  const winRate = summary?.winRate ?? 50;

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-dark-700/50 bg-dark-900/60 px-4 py-2.5">
      <div className="flex items-center gap-1.5 mr-2">
        <Eye className="h-3.5 w-3.5 text-dark-400" />
        <span className="text-xs font-medium text-dark-400">vs {opponentName}</span>
      </div>

      {pills.map((t, i) => {
        const isActive = activeFilter === t.filter;
        return (
          <button
            key={i}
            type="button"
            onClick={() => onTagFilter?.(isActive ? null : t.filter)}
            className={isActive ? 'ring-2 ring-forge-400 rounded-full' : ''}
            title={`Filter plays by ${t.filter}`}
          >
            <Badge variant={t.variant} size="sm">
              {t.label}
            </Badge>
          </button>
        );
      })}

      {activeFilter && onTagFilter && (
        <button
          type="button"
          onClick={() => onTagFilter(null)}
          className="inline-flex items-center gap-1 text-[10px] text-dark-400 hover:text-dark-200"
        >
          <X className="h-3 w-3" /> clear
        </button>
      )}

      <span className="rounded-full border border-purple-500/30 bg-purple-500/10 px-2.5 py-0.5 text-[10px] font-bold text-purple-400">
        {archetypeLabel}
      </span>

      <span className="ml-auto rounded-md border border-forge-500/30 bg-forge-500/10 px-2 py-0.5 text-[11px] font-bold tabular-nums text-forge-400">
        Win Rate: {winRate}%
      </span>
    </div>
  );
}

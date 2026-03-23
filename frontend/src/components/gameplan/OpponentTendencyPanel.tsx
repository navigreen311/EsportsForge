'use client';

import { useState } from 'react';
import { clsx } from 'clsx';
import { Eye, ChevronDown } from 'lucide-react';
import { Badge } from '@/components/shared/Badge';

interface OpponentTendencyPanelProps {
  opponentName: string;
  onFilterByTendency?: (tendency: string) => void;
}

const tendencyPills = [
  { label: 'Cover 2: 68%', variant: 'info' as const, key: 'cover-2' },
  { label: 'Blitzes: 34%', variant: 'danger' as const, key: 'blitzes' },
  { label: 'Run-first 3rd: 71%', variant: 'warning' as const, key: 'run-first-3rd' },
];

interface BreakdownRow {
  label: string;
  pct: number;
}

const coverageBreakdown: BreakdownRow[] = [
  { label: 'Cover 2', pct: 68 },
  { label: 'Cover 3', pct: 21 },
  { label: 'Man', pct: 11 },
];

const pressureBreakdown: BreakdownRow[] = [
  { label: 'Blitz', pct: 34 },
  { label: 'Zone Blitz', pct: 12 },
  { label: 'No Blitz', pct: 54 },
];

const downTendencies: BreakdownRow[] = [
  { label: '1st down pass', pct: 58 },
  { label: '3rd-short run', pct: 71 },
];

function PercentageBar({ label, pct }: BreakdownRow) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 shrink-0 text-xs text-dark-400">{label}</span>
      <div className="h-1.5 flex-1 rounded-full bg-dark-700/50">
        <div
          className="h-1.5 rounded-full bg-forge-500/60"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-10 shrink-0 text-right text-xs font-medium text-dark-300">
        {pct}%
      </span>
    </div>
  );
}

export default function OpponentTendencyPanel({
  opponentName,
  onFilterByTendency,
}: OpponentTendencyPanelProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={clsx(
        'rounded-lg border border-dark-700/50 bg-dark-900/60 px-4 py-2',
        expanded && 'pb-4'
      )}
    >
      {/* Collapsed header row */}
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        className="flex w-full items-center gap-3"
      >
        <Eye className="h-3.5 w-3.5 text-dark-400" />
        <span className="text-xs font-medium text-dark-400">
          Opponent Intel Summary
        </span>

        {/* Tendency pills */}
        <div className="flex items-center gap-2">
          {tendencyPills.map((pill) => (
            <span
              key={pill.key}
              role="button"
              tabIndex={0}
              onClick={(e) => {
                e.stopPropagation();
                onFilterByTendency?.(pill.key);
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.stopPropagation();
                  onFilterByTendency?.(pill.key);
                }
              }}
              className="cursor-pointer transition-opacity hover:opacity-80"
            >
              <Badge variant={pill.variant} size="sm">
                {pill.label}
              </Badge>
            </span>
          ))}
        </div>

        <ChevronDown
          className={clsx(
            'ml-auto h-4 w-4 text-dark-400 transition-transform duration-200',
            expanded && 'rotate-180'
          )}
        />
      </button>

      {/* Expanded detail grid */}
      {expanded && (
        <div className="mt-4 grid gap-6 sm:grid-cols-3">
          {/* Coverage */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-dark-400">
              Coverage
            </h4>
            {coverageBreakdown.map((row) => (
              <PercentageBar key={row.label} {...row} />
            ))}
          </div>

          {/* Pressure */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-dark-400">
              Pressure
            </h4>
            {pressureBreakdown.map((row) => (
              <PercentageBar key={row.label} {...row} />
            ))}
          </div>

          {/* Down Tendencies */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-dark-400">
              Down Tendencies
            </h4>
            {downTendencies.map((row) => (
              <PercentageBar key={row.label} {...row} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

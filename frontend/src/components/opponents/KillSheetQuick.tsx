'use client';

import { useState } from 'react';
import { Crosshair, ChevronDown, Trophy } from 'lucide-react';
import type { KillSheetPlay } from '@/types/opponent';

interface KillSheetQuickProps {
  plays: KillSheetPlay[];
  opponentName: string;
}

/**
 * Collapsible top-3 kill sheet plays with win rates.
 * Designed for inline use in the opponent dossier page.
 */
export default function KillSheetQuick({ plays, opponentName }: KillSheetQuickProps) {
  const [expanded, setExpanded] = useState(true);
  const top3 = plays.slice(0, 3);

  if (top3.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50">
      {/* Header — clickable to collapse */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-6 py-4 text-left"
      >
        <div className="flex items-center gap-3">
          <Crosshair className="h-5 w-5 text-forge-400" />
          <div>
            <h2 className="text-lg font-semibold text-dark-50">
              Quick Kill Sheet
            </h2>
            <p className="text-sm text-dark-400">
              Top 3 plays that beat {opponentName}
            </p>
          </div>
        </div>
        <ChevronDown
          className={`h-5 w-5 text-dark-400 transition-transform duration-200 ${
            expanded ? 'rotate-180' : ''
          }`}
        />
      </button>

      {/* Content */}
      {expanded && (
        <div className="border-t border-dark-700 px-6 py-4 space-y-3">
          {top3.map((play, i) => {
            const isTop = i === 0;
            return (
              <div
                key={play.id}
                className="flex items-center gap-4 rounded-lg bg-dark-800/50 border border-dark-700 p-3"
              >
                {/* Rank */}
                <span
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-sm font-bold ${
                    isTop
                      ? 'bg-forge-500/20 text-forge-400 border border-forge-800/30'
                      : 'bg-dark-700 text-dark-300 border border-dark-600'
                  }`}
                >
                  {i + 1}
                </span>

                {/* Play info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-dark-100 truncate">
                      {play.playName}
                    </span>
                    {isTop && (
                      <Trophy className="h-3.5 w-3.5 text-yellow-400 shrink-0" />
                    )}
                  </div>
                  <span className="text-xs text-dark-500">{play.formation}</span>
                </div>

                {/* Win rate bar */}
                <div className="flex items-center gap-3 shrink-0">
                  <div className="w-20">
                    <div className="h-1.5 w-full rounded-full bg-dark-700">
                      <div
                        className={`h-1.5 rounded-full transition-all duration-500 ${
                          play.successRate >= 70
                            ? 'bg-forge-500'
                            : play.successRate >= 50
                              ? 'bg-amber-500'
                              : 'bg-red-500'
                        }`}
                        style={{ width: `${play.successRate}%` }}
                      />
                    </div>
                  </div>
                  <span
                    className={`text-sm font-bold font-mono ${
                      play.successRate >= 70
                        ? 'text-forge-400'
                        : play.successRate >= 50
                          ? 'text-amber-400'
                          : 'text-red-400'
                    }`}
                  >
                    {play.successRate}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

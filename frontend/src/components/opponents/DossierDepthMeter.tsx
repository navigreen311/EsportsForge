'use client';

import { Signal } from 'lucide-react';
import type { Opponent } from '@/types/opponent';

interface DossierDepthMeterProps {
  opponent: Opponent;
}

/**
 * Signal-strength visual meter for dossier completeness.
 * Displays 5 bars like a Wi-Fi / cellular signal icon.
 */
export default function DossierDepthMeter({ opponent }: DossierDepthMeterProps) {
  const score = calculateDepth(opponent);
  const bars = 5;
  const filledBars = Math.min(bars, Math.ceil((score / 10) * bars));

  const barColor =
    filledBars >= 4
      ? 'bg-forge-400'
      : filledBars >= 2
        ? 'bg-amber-400'
        : 'bg-red-400';

  const label =
    filledBars >= 4
      ? 'Strong signal'
      : filledBars >= 2
        ? 'Moderate signal'
        : 'Weak signal';

  return (
    <div className="flex items-center gap-2" title={`Dossier depth: ${score}/10 — ${label}`}>
      <Signal className="h-4 w-4 text-dark-400" />
      <div className="flex items-end gap-0.5">
        {Array.from({ length: bars }).map((_, i) => {
          const height = 4 + i * 3; // 4px, 7px, 10px, 13px, 16px
          const filled = i < filledBars;
          return (
            <div
              key={i}
              className={`w-1.5 rounded-sm transition-colors ${
                filled ? barColor : 'bg-dark-700'
              }`}
              style={{ height: `${height}px` }}
            />
          );
        })}
      </div>
      <span className="text-xs text-dark-400">{score}/10</span>
    </div>
  );
}

function calculateDepth(opponent: Opponent): number {
  let score = 0;
  if (opponent.encounterCount >= 2) score += 1;
  if (opponent.encounterCount >= 5) score += 1;
  if (opponent.encounterCount >= 8) score += 1;
  if (opponent.tendencies.length > 0) score += 1;
  if (opponent.blitzFrequency > 0) score += 1;
  if (opponent.behavioralSignals.length >= 2) score += 1;
  if (opponent.killSheet.length >= 3) score += 1;
  if (opponent.weaknesses.length >= 2) score += 1;
  if (opponent.formationFrequencies.length > 0) score += 1;
  if (opponent.encounters.length > 0) score += 1;
  return score;
}

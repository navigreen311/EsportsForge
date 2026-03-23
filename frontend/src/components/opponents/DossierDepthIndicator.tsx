'use client';

import type { Opponent } from '@/types/opponent';

interface DossierDepthIndicatorProps {
  opponent: Opponent;
}

function calculateDossierScore(opponent: Opponent): {
  score: number;
  missing: string[];
} {
  let score = 0;
  const missing: string[] = [];

  // 1. Games played tiers
  if (opponent.encounterCount >= 2) score += 1;
  else missing.push('Play 2+ games');

  if (opponent.encounterCount >= 5) score += 1;
  else if (opponent.encounterCount < 5) missing.push('Play 5+ games');

  if (opponent.encounterCount >= 8) score += 1;
  else if (opponent.encounterCount < 8) missing.push('Play 8+ games');

  // 2. Coverage tendency data
  if (opponent.tendencies.length > 0) {
    score += 1;
  } else {
    missing.push('Coverage tendency data');
  }

  // 3. Blitz data
  if (opponent.blitzFrequency > 0) {
    score += 1;
  } else {
    missing.push('Blitz frequency data');
  }

  // 4. Behavioral signals (>= 2)
  if (opponent.behavioralSignals.length >= 2) {
    score += 1;
  } else {
    missing.push('2+ behavioral signals');
  }

  // 5. Kill sheet (>= 3 plays)
  if (opponent.killSheet.length >= 3) {
    score += 1;
  } else {
    missing.push('3+ kill sheet plays');
  }

  // 6. Weaknesses (>= 2)
  if (opponent.weaknesses.length >= 2) {
    score += 1;
  } else {
    missing.push('2+ identified weaknesses');
  }

  // 7. Formation frequencies
  if (opponent.formationFrequencies.length > 0) {
    score += 1;
  } else {
    missing.push('Formation frequency data');
  }

  // 8. Encounter history
  if (opponent.encounters.length > 0) {
    score += 1;
  } else {
    missing.push('Encounter history');
  }

  return { score, missing };
}

function getBarColor(score: number): string {
  if (score >= 8) return 'bg-forge-500';
  if (score >= 5) return 'bg-amber-500';
  return 'bg-red-500';
}

export default function DossierDepthIndicator({
  opponent,
}: DossierDepthIndicatorProps) {
  if (!opponent.isRival) return null;

  const { score, missing } = calculateDossierScore(opponent);
  const fillPercent = (score / 10) * 100;
  const barColor = getBarColor(score);

  const tooltip =
    missing.length > 0
      ? `Missing: ${missing.join(', ')}`
      : 'Dossier complete!';

  return (
    <span
      className="inline-flex items-center gap-1.5 text-[10px] text-dark-400"
      title={tooltip}
    >
      <span>Dossier: {score}/10</span>
      <span className="h-1 w-16 rounded-full bg-dark-700">
        <span
          className={`block h-1 rounded-full ${barColor}`}
          style={{ width: `${fillPercent}%` }}
        />
      </span>
    </span>
  );
}

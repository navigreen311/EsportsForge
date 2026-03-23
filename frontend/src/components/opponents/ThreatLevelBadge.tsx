'use client';

import { AlertTriangle } from 'lucide-react';
import clsx from 'clsx';
import type { Opponent } from '@/types/opponent';

/**
 * Calculate a 0–100 threat score for a given opponent.
 *
 * Components:
 *  - Win-rate trend (how poorly we perform against them)
 *  - Recency (how recently we faced them)
 *  - Archetype difficulty
 *  - Rival tier (based on isRival flag + encounter count)
 */
export function calculateThreatLevel(opponent: Opponent): number {
  let score = 0;

  // --- Win-rate trend component ---
  if (opponent.winRate < 40) {
    score += 30;
  } else if (opponent.winRate < 50) {
    score += 20;
  } else if (opponent.winRate < 60) {
    score += 10;
  }

  // --- Recency component ---
  const recency = parseRecency(opponent.lastSeen);
  score += recency;

  // --- Archetype difficulty component ---
  score += archetypeDifficulty(opponent.archetype);

  // --- Rival tier component ---
  if (opponent.isRival) {
    if (opponent.encounterCount >= 8) {
      score += 20; // Nemesis
    } else if (opponent.encounterCount >= 5) {
      score += 15; // Arch-Rival
    } else if (opponent.encounterCount >= 2) {
      score += 10;
    }
  }

  return Math.min(score, 100);
}

function parseRecency(lastSeen: string): number {
  if (lastSeen.includes('2d')) return 28;
  if (lastSeen.includes('1w')) return 20;
  if (lastSeen.includes('2w')) return 10;
  if (lastSeen.includes('3w')) return 5;
  return 0;
}

function archetypeDifficulty(archetype: string): number {
  switch (archetype) {
    case 'Aggressive Rusher':
    case 'Blitz Heavy':
      return 15;
    case 'Air Raid':
      return 12;
    case 'Scrambler':
      return 10;
    default:
      return 5;
  }
}

// ---------------------------------------------------------------------------
// Badge component
// ---------------------------------------------------------------------------

interface ThreatLevelBadgeProps {
  opponent: Opponent;
}

export function ThreatLevelBadge({ opponent }: ThreatLevelBadgeProps) {
  const level = calculateThreatLevel(opponent);

  const isHigh = level >= 75;
  const isMedium = level >= 50;

  const label = isHigh ? 'HIGH THREAT' : isMedium ? 'MEDIUM' : 'LOW';

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase',
        isHigh && 'bg-red-500/20 text-red-400 border-red-500/30',
        !isHigh && isMedium && 'bg-amber-500/20 text-amber-400 border-amber-500/30',
        !isMedium && 'bg-dark-700/50 text-dark-300 border-dark-600/50',
      )}
    >
      {isHigh && <AlertTriangle className="h-3 w-3" />}
      {label}
    </span>
  );
}

'use client';

import { Clock } from 'lucide-react';

interface RecencyDecayWarningProps {
  lastSeen: string;
}

interface StaleDataHeaderProps {
  lastSeen: string;
  children: React.ReactNode;
}

/**
 * Determines whether scouting data is stale based on the lastSeen string.
 * Stale = 2+ weeks old. Strings like "2w ago", "3w ago" are stale;
 * "1w ago", "5d ago" are not.
 */
export function isDataStale(lastSeen: string): boolean {
  const weekMatch = lastSeen.match(/(\d+)w/);
  if (weekMatch) {
    return parseInt(weekMatch[1], 10) >= 2;
  }
  return false;
}

/**
 * Renders a small amber Clock icon with a staleness tooltip when scouting
 * data is >= 2 weeks old. Returns null otherwise.
 */
export default function RecencyDecayWarning({ lastSeen }: RecencyDecayWarningProps) {
  if (!isDataStale(lastSeen)) return null;

  return (
    <span
      title="Scouting data may be stale — tendencies can shift over multiple weeks. Consider re-scouting before next matchup."
      className="inline-flex items-center"
    >
      <Clock className="h-3.5 w-3.5 text-amber-400" />
    </span>
  );
}

/**
 * Wraps children with an amber-tinted header when scouting data is stale.
 * Renders children as-is when data is fresh.
 */
export function StaleDataHeader({ lastSeen, children }: StaleDataHeaderProps) {
  if (!isDataStale(lastSeen)) {
    return <>{children}</>;
  }

  return (
    <div className="text-amber-400">
      {children}
      <span className="ml-1 text-[10px] text-amber-400 font-medium">
        (data may be stale)
      </span>
    </div>
  );
}

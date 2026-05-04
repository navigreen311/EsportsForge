/**
 * Reusable Offense/Defense toggle.
 *
 * Used across Arsenal, Gameplan, Drill Lab, Analytics, and SimLab so the
 * visual + interaction is consistent everywhere. Offense = sword + green
 * accent. Defense = shield + sky-blue accent.
 */

'use client';

import { Swords, Shield } from 'lucide-react';
import { clsx } from 'clsx';

export type WeaponSide = 'offense' | 'defense';

interface Props {
  side: WeaponSide;
  onChange: (side: WeaponSide) => void;
  /** Override the default 'Offense' / 'Defense' labels when the title
   *  prefers different naming (e.g. "Pitching & Fielding" for MLB). */
  offenseLabel?: string;
  defenseLabel?: string;
  /** When set, only the labelled side is rendered as enabled and the other
   *  is shown disabled. Used in places where defense isn't supported yet
   *  for a particular title. */
  disabledSide?: WeaponSide;
  className?: string;
}

export function SideToggle({
  side,
  onChange,
  offenseLabel = 'Offense',
  defenseLabel = 'Defense',
  disabledSide,
  className,
}: Props) {
  return (
    <div
      className={clsx(
        'inline-flex items-center gap-1 rounded-lg border border-dark-700/50 bg-dark-900/60 p-1',
        className
      )}
      role="tablist"
      aria-label="Offense vs Defense"
    >
      <button
        type="button"
        role="tab"
        aria-selected={side === 'offense'}
        disabled={disabledSide === 'offense'}
        onClick={() => onChange('offense')}
        className={clsx(
          'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-bold transition-colors disabled:cursor-not-allowed disabled:opacity-40',
          side === 'offense'
            ? 'bg-forge-500/15 text-forge-300'
            : 'text-dark-400 hover:text-dark-200'
        )}
      >
        <Swords className="h-3.5 w-3.5" />
        {offenseLabel}
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={side === 'defense'}
        disabled={disabledSide === 'defense'}
        onClick={() => onChange('defense')}
        className={clsx(
          'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-bold transition-colors disabled:cursor-not-allowed disabled:opacity-40',
          side === 'defense'
            ? 'bg-sky-500/15 text-sky-300'
            : 'text-dark-400 hover:text-dark-200'
        )}
      >
        <Shield className="h-3.5 w-3.5" />
        {defenseLabel}
      </button>
    </div>
  );
}

/**
 * Title-aware label override — defensive label is "Pitching & Fielding"
 * for baseball, "Course Management" for golf, etc. Mirrors the
 * `TITLE_DEFENSE_CONTEXT` server-side data.
 */
export const DEFENSE_LABEL_BY_TITLE: Record<string, string> = {
  'mlb-26': 'Pitching & Fielding',
  'pga-2k25': 'Course Management',
  'video-poker': 'Risk Management',
  'warzone': 'Defensive Tactics',
  'fortnite': 'Defensive Building',
  'ufc-5': 'Defense & Grappling',
};

/**
 * "Weapons Ready for This Matchup" card for the War Room.
 * Shows the player's saved weapons for the active title.
 */

'use client';

import { Zap, ChevronRight } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useMyArsenal } from '@/hooks/useArsenal';

export function WeaponSummaryCard() {
  const router = useRouter();
  const { data: weapons = [] } = useMyArsenal();

  if (weapons.length === 0) return null;

  return (
    <div className="rounded-xl border border-forge-500/30 bg-emerald-950/20 p-5">
      <div className="mb-3 flex items-start gap-3">
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-forge-500/15">
          <Zap className="h-5 w-5 text-forge-400" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-dark-100">
            Weapons Ready for This Matchup
          </h3>
          <p className="text-[11px] text-dark-400">
            ArsenalAI has identified {weapons.length} high-value deployment{' '}
            {weapons.length === 1 ? 'window' : 'windows'} vs this opponent
          </p>
        </div>
      </div>

      <ul className="space-y-2">
        {weapons.slice(0, 3).map((w) => (
          <li
            key={w.id}
            className="flex items-start gap-2 rounded-md bg-dark-900/40 px-3 py-2 text-xs"
          >
            <Zap className="mt-0.5 h-3 w-3 flex-shrink-0 text-forge-400" />
            <div className="min-w-0 flex-1">
              <p className="font-semibold text-dark-100">{w.name}</p>
              <p className="text-[11px] text-dark-400">
                <span className="text-forge-300">→ </span>
                {w.when_to_use}
              </p>
            </div>
          </li>
        ))}
      </ul>

      <button
        type="button"
        onClick={() => router.push('/arsenal')}
        className="mt-3 inline-flex items-center gap-1 text-[11px] font-bold text-forge-300 hover:text-forge-200"
      >
        View All Arsenal Weapons
        <ChevronRight className="h-3 w-3" />
      </button>
    </div>
  );
}

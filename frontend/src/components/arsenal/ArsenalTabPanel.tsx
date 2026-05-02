/**
 * Gameplan Arsenal tab — saved weapons for the active title with quick
 * deploy-condition pills. Click a weapon to open the slide-over detail.
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Zap, ExternalLink } from 'lucide-react';
import { useMyArsenal } from '@/hooks/useArsenal';
import { WeaponDetail } from './WeaponDetail';

const TOP_KEYS = ['down', 'distance', 'opponentTendency', 'shotClock', 'count', 'circlePhase', 'storm', 'wind', 'lie', 'round', 'stamina', 'hand'];

function deployPills(triggers: Record<string, unknown>): string[] {
  const out: string[] = [];
  for (const k of TOP_KEYS) {
    const v = (triggers as Record<string, unknown>)[k];
    if (v === undefined || v === null) continue;
    const label =
      Array.isArray(v) || typeof v === 'object' ? JSON.stringify(v) : String(v);
    out.push(`${k}: ${label}`);
    if (out.length >= 3) break;
  }
  // also surface any *_max / *_min keys
  if (out.length < 3) {
    for (const [k, v] of Object.entries(triggers)) {
      if (!k.endsWith('_min') && !k.endsWith('_max')) continue;
      out.push(`${k}: ${String(v)}`);
      if (out.length >= 3) break;
    }
  }
  return out;
}

export function ArsenalTabPanel() {
  const { data: weapons = [], isLoading } = useMyArsenal();
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between gap-2">
        <div>
          <h3 className="text-sm font-bold text-dark-100">
            Your Secret Weapons — deploy these at the right moment
          </h3>
          <p className="text-[11px] text-dark-400">
            Saved weapons for this title; click for full setup steps.
          </p>
        </div>
        <Link
          href="/arsenal"
          className="inline-flex items-center gap-1 rounded-md border border-dark-700 bg-dark-800 px-3 py-1.5 text-[11px] font-medium text-dark-200 hover:bg-dark-700"
        >
          Open Arsenal
          <ExternalLink className="h-3 w-3" />
        </Link>
      </div>

      {isLoading ? (
        <div className="rounded-xl border border-dark-700 bg-dark-900/60 p-6 text-center text-sm text-dark-400">
          Loading saved weapons…
        </div>
      ) : weapons.length === 0 ? (
        <div className="rounded-xl border border-dark-700 bg-dark-900/60 p-6 text-center text-sm text-dark-400">
          No weapons saved for this title yet.{' '}
          <Link href="/arsenal" className="text-forge-300 hover:underline">
            Browse the library
          </Link>
        </div>
      ) : (
        <ul className="space-y-2">
          {weapons.map((w) => (
            <li
              key={w.id}
              className="rounded-lg border border-dark-700 bg-dark-900/60 p-3"
            >
              <div className="flex items-start gap-3">
                <Zap className="mt-0.5 h-4 w-4 flex-shrink-0 text-forge-400" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-bold text-dark-100">{w.name}</p>
                  <p className="text-[11px] text-dark-400">{w.when_to_use}</p>
                  {(() => {
                    const pills = deployPills(w.trigger_conditions ?? {});
                    return pills.length > 0 ? (
                      <div className="mt-1.5 flex flex-wrap gap-1">
                        <span className="text-[10px] text-dark-500">
                          Deploy when:
                        </span>
                        {pills.map((p) => (
                          <span
                            key={p}
                            className="rounded-full border border-forge-500/30 bg-forge-500/10 px-2 py-0.5 text-[10px] text-forge-300"
                          >
                            {p}
                          </span>
                        ))}
                      </div>
                    ) : null;
                  })()}
                </div>
                <button
                  type="button"
                  onClick={() => setOpenId(w.id)}
                  className="rounded-md border border-dark-700 bg-dark-800 px-2 py-1 text-[11px] font-medium text-dark-200 hover:bg-dark-700"
                >
                  View Full Setup
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <WeaponDetail weaponId={openId} onClose={() => setOpenId(null)} />
    </div>
  );
}

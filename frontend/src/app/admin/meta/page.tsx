/**
 * Admin Meta Content Pipeline (F16) — weekly meta weapon entries per title,
 * with AI generation and publish controls.
 */

'use client';

import { useState } from 'react';
import { Swords, Sparkles, Send, ChevronDown } from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Types & mock data                                                  */
/* ------------------------------------------------------------------ */

interface MetaWeapon {
  id: string;
  weapon: string;
  whyStrong: string;
  counter: string;
  counterWhy: string;
  strengthRating: number; // 1-10
}

interface MetaWeek {
  weekLabel: string;
  weekId: string;
  title: string;
  status: 'draft' | 'published';
  weapons: MetaWeapon[];
}

const MOCK_WEEKS: MetaWeek[] = [
  {
    weekLabel: 'Week 15 (Apr 7 – Apr 13)',
    weekId: 'w15-2026',
    title: 'Madden 26',
    status: 'draft',
    weapons: [
      { id: 'm1', weapon: 'Gun Bunch – HB Wheel', whyStrong: 'Creates 5 mismatches vs Cover 3', counter: 'Tampa 2 Robber', counterWhy: 'Safety drops into seam, LB walls flat', strengthRating: 9 },
      { id: 'm2', weapon: 'Nickel 3-3-5 Wide', whyStrong: 'Best blitz coverage disguise', counter: 'Singleback Ace HB Dive', counterWhy: 'Undersized front can\'t stop inside runs', strengthRating: 8 },
      { id: 'm3', weapon: 'RPO Alert Bubble', whyStrong: 'Forces LB conflict every snap', counter: 'Man Blitz Press', counterWhy: 'Press eliminates bubble window', strengthRating: 7 },
    ],
  },
  {
    weekLabel: 'Week 15 (Apr 7 – Apr 13)',
    weekId: 'w15-2026-cfb',
    title: 'CFB 26',
    status: 'published',
    weapons: [
      { id: 'c1', weapon: 'Spread RPO Read', whyStrong: 'Exploits slow LB keys in college AI', counter: 'Quarters Coverage', counterWhy: 'Safety fills run lane immediately', strengthRating: 8 },
      { id: 'c2', weapon: 'Bear Front Pinch', whyStrong: 'Clogs A/B gaps vs spread', counter: 'Outside Zone Weak', counterWhy: 'Tackles seal edge against pinched front', strengthRating: 7 },
    ],
  },
  {
    weekLabel: 'Week 14 (Mar 31 – Apr 6)',
    weekId: 'w14-2026',
    title: 'Madden 26',
    status: 'published',
    weapons: [
      { id: 'm4', weapon: 'Singleback Ace PA Boot', whyStrong: 'High/low read vs zone, TE drag open', counter: 'Cover 4 Palms', counterWhy: 'Pattern-match eliminates crossers', strengthRating: 8 },
    ],
  },
];

const STATUS_BADGE: Record<string, string> = {
  draft:     'bg-amber-500/10 text-amber-400',
  published: 'bg-green-500/10 text-green-400',
};

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function AdminMetaPage() {
  const [selectedWeek, setSelectedWeek] = useState(MOCK_WEEKS[0].weekId);

  const currentWeeks = MOCK_WEEKS.filter((w) => w.weekId === selectedWeek || selectedWeek === 'all');
  const uniqueWeeks = [...new Map(MOCK_WEEKS.map((w) => [w.weekId, w.weekLabel])).entries()];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Swords className="h-6 w-6 text-forge-400" />
        <h1 className="text-2xl font-bold text-dark-50">Meta Content Pipeline</h1>
      </div>

      {/* Week Selector */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative">
          <select
            value={selectedWeek}
            onChange={(e) => setSelectedWeek(e.target.value)}
            className="appearance-none rounded-lg border border-dark-700 bg-dark-800 py-2 pl-4 pr-10 text-sm text-dark-100 focus:border-forge-400 focus:outline-none focus:ring-1 focus:ring-forge-400"
          >
            <option value="all">All Weeks</option>
            {uniqueWeeks.map(([id, label]) => (
              <option key={id} value={id}>{label}</option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-500" />
        </div>
      </div>

      {/* Per-title cards */}
      {(selectedWeek === 'all' ? MOCK_WEEKS : MOCK_WEEKS.filter((w) => w.weekId === selectedWeek)).map((week) => (
        <div
          key={`${week.weekId}-${week.title}`}
          className="rounded-xl border border-dark-700/60 bg-dark-900 p-5"
        >
          {/* Header */}
          <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-sm font-semibold text-dark-100">{week.title}</h2>
              <p className="text-xs text-dark-400">{week.weekLabel}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_BADGE[week.status]}`}>
                {week.status}
              </span>
              <button className="flex items-center gap-1.5 rounded-lg bg-dark-800 px-3 py-1.5 text-xs font-medium text-dark-300 transition-colors hover:bg-dark-700 hover:text-dark-100">
                <Sparkles className="h-3.5 w-3.5" />
                Generate via AI
              </button>
              <button className="flex items-center gap-1.5 rounded-lg bg-forge-400/10 px-3 py-1.5 text-xs font-medium text-forge-400 transition-colors hover:bg-forge-400/20">
                <Send className="h-3.5 w-3.5" />
                Publish
              </button>
            </div>
          </div>

          {/* Weapons Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-dark-700/60 text-left text-xs text-dark-400">
                  <th className="px-4 py-3 font-medium">Weapon</th>
                  <th className="px-4 py-3 font-medium">Why Strong</th>
                  <th className="px-4 py-3 font-medium">Counter</th>
                  <th className="px-4 py-3 font-medium">Counter Why</th>
                  <th className="px-4 py-3 font-medium">Strength</th>
                </tr>
              </thead>
              <tbody>
                {week.weapons.map((w) => (
                  <tr
                    key={w.id}
                    className="border-b border-dark-700/30 transition-colors hover:bg-dark-800/40"
                  >
                    <td className="px-4 py-3 font-medium text-dark-100">{w.weapon}</td>
                    <td className="max-w-[200px] px-4 py-3 text-dark-300">{w.whyStrong}</td>
                    <td className="px-4 py-3 text-dark-100">{w.counter}</td>
                    <td className="max-w-[200px] px-4 py-3 text-dark-300">{w.counterWhy}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-16 overflow-hidden rounded-full bg-dark-700">
                          <div
                            className="h-full rounded-full bg-forge-400"
                            style={{ width: `${w.strengthRating * 10}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-dark-300">
                          {w.strengthRating}/10
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}

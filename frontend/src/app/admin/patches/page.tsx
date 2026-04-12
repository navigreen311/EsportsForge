/**
 * Admin Patch Tracking (F17) — log game patches, track impact on recommendations.
 */

'use client';

import { useState } from 'react';
import { FileText, Plus, AlertTriangle, X } from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Types & mock data                                                  */
/* ------------------------------------------------------------------ */

interface Patch {
  id: string;
  title: string;
  version: string;
  releaseDate: string;
  impact: 'low' | 'medium' | 'high' | 'critical';
  keyChanges: string;
  status: 'logged' | 'reviewed' | 'applied';
  staleRecommendations: number;
}

const MOCK_PATCHES: Patch[] = [
  {
    id: 'p1',
    title: 'Madden 26',
    version: '1.4.2',
    releaseDate: '2026-04-10',
    impact: 'high',
    keyChanges: 'Zone coverage AI rework, RPO timing nerf, HB screen route adjustment',
    status: 'logged',
    staleRecommendations: 47,
  },
  {
    id: 'p2',
    title: 'CFB 26',
    version: '2.1.0',
    releaseDate: '2026-04-05',
    impact: 'medium',
    keyChanges: 'Option read timing fix, recruiting UI update, playoff bracket adjustments',
    status: 'reviewed',
    staleRecommendations: 12,
  },
  {
    id: 'p3',
    title: 'NBA 2K26',
    version: '1.08',
    releaseDate: '2026-03-28',
    impact: 'critical',
    keyChanges: 'Shot timing overhaul, dribble move speed adjustments, build attribute rebalance',
    status: 'applied',
    staleRecommendations: 0,
  },
  {
    id: 'p4',
    title: 'EA FC 26',
    version: '6.1',
    releaseDate: '2026-03-20',
    impact: 'low',
    keyChanges: 'Kit updates, minor goalkeeper positioning fix',
    status: 'applied',
    staleRecommendations: 0,
  },
];

const IMPACT_BADGE: Record<Patch['impact'], string> = {
  low:      'bg-dark-700 text-dark-300',
  medium:   'bg-amber-500/10 text-amber-400',
  high:     'bg-orange-500/10 text-orange-400',
  critical: 'bg-red-500/10 text-red-400',
};

const STATUS_BADGE: Record<Patch['status'], string> = {
  logged:   'bg-amber-500/10 text-amber-400',
  reviewed: 'bg-blue-500/10 text-blue-400',
  applied:  'bg-green-500/10 text-green-400',
};

const TITLES = ['Madden 26', 'CFB 26', 'NBA 2K26', 'EA FC 26', 'MLB 26', 'UFC 5', 'Warzone', 'Fortnite', 'PGA 2K25'];

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function AdminPatchesPage() {
  const [showForm, setShowForm] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <FileText className="h-6 w-6 text-forge-400" />
        <h1 className="text-2xl font-bold text-dark-50">Patch Tracking</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="ml-auto flex items-center gap-1.5 rounded-lg bg-forge-400/10 px-3 py-2 text-xs font-medium text-forge-400 transition-colors hover:bg-forge-400/20"
        >
          {showForm ? <X className="h-3.5 w-3.5" /> : <Plus className="h-3.5 w-3.5" />}
          {showForm ? 'Cancel' : 'Add Patch'}
        </button>
      </div>

      {/* Add Patch Form */}
      {showForm && (
        <div className="rounded-xl border border-dark-700/60 bg-dark-900 p-5">
          <h2 className="mb-4 text-sm font-semibold text-dark-100">Log New Patch</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="mb-1 block text-xs text-dark-400">Title</label>
              <select className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-100 focus:border-forge-400 focus:outline-none focus:ring-1 focus:ring-forge-400">
                <option value="">Select title...</option>
                {TITLES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-dark-400">Version</label>
              <input
                type="text"
                placeholder="e.g. 1.4.3"
                className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-100 placeholder-dark-500 focus:border-forge-400 focus:outline-none focus:ring-1 focus:ring-forge-400"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-dark-400">Release Date</label>
              <input
                type="date"
                className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-100 focus:border-forge-400 focus:outline-none focus:ring-1 focus:ring-forge-400"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-dark-400">Impact</label>
              <select className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-100 focus:border-forge-400 focus:outline-none focus:ring-1 focus:ring-forge-400">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>
          <div className="mt-4">
            <label className="mb-1 block text-xs text-dark-400">Key Changes</label>
            <textarea
              rows={3}
              placeholder="Describe what changed..."
              className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-100 placeholder-dark-500 focus:border-forge-400 focus:outline-none focus:ring-1 focus:ring-forge-400"
            />
          </div>
          <div className="mt-4 flex justify-end">
            <button className="rounded-lg bg-forge-400 px-4 py-2 text-sm font-medium text-dark-950 transition-colors hover:bg-forge-300">
              Save Patch
            </button>
          </div>
        </div>
      )}

      {/* Patches Table */}
      <div className="overflow-x-auto rounded-xl border border-dark-700/60 bg-dark-900">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700/60 text-left text-xs text-dark-400">
              <th className="px-4 py-3 font-medium">Title</th>
              <th className="px-4 py-3 font-medium">Version</th>
              <th className="px-4 py-3 font-medium">Release Date</th>
              <th className="px-4 py-3 font-medium">Impact</th>
              <th className="px-4 py-3 font-medium">Key Changes</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Stale Recs</th>
            </tr>
          </thead>
          <tbody>
            {MOCK_PATCHES.map((p) => (
              <tr
                key={p.id}
                className="border-b border-dark-700/30 transition-colors hover:bg-dark-800/40"
              >
                <td className="px-4 py-3 font-medium text-dark-100">{p.title}</td>
                <td className="px-4 py-3 font-mono text-xs text-dark-300">{p.version}</td>
                <td className="px-4 py-3 text-dark-300">{p.releaseDate}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${IMPACT_BADGE[p.impact]}`}>
                    {p.impact}
                  </span>
                </td>
                <td className="max-w-[280px] px-4 py-3 text-dark-300">{p.keyChanges}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_BADGE[p.status]}`}>
                    {p.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {p.staleRecommendations > 0 ? (
                    <span className="flex items-center gap-1 text-amber-400">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      <span className="text-xs font-medium">{p.staleRecommendations}</span>
                    </span>
                  ) : (
                    <span className="text-xs text-dark-500">0</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Admin Users — searchable, filterable user management table.
 */

'use client';

import { useState, useMemo } from 'react';
import { Users, Search, Eye, RefreshCw, Ban } from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Mock data                                                          */
/* ------------------------------------------------------------------ */

interface MockUser {
  id: string;
  email: string;
  username: string;
  tier: 'free' | 'competitive' | 'elite' | 'team';
  activeTitle: string | null;
  lastLogin: string;
  joined: string;
}

const MOCK_USERS: MockUser[] = [
  { id: '1', email: 'alex@example.com',     username: 'AlexGrind',    tier: 'elite',       activeTitle: 'Madden 26',   lastLogin: '2026-04-12', joined: '2025-11-03' },
  { id: '2', email: 'jordan@example.com',   username: 'JMoney99',     tier: 'competitive', activeTitle: 'CFB 26',      lastLogin: '2026-04-11', joined: '2025-12-18' },
  { id: '3', email: 'sam@example.com',       username: 'SamSlam',      tier: 'free',        activeTitle: null,          lastLogin: '2026-04-08', joined: '2026-01-22' },
  { id: '4', email: 'taylor@example.com',   username: 'TaylorMade',   tier: 'team',        activeTitle: 'NBA 2K26',    lastLogin: '2026-04-12', joined: '2025-09-14' },
  { id: '5', email: 'casey@example.com',     username: 'CaseyW',       tier: 'elite',       activeTitle: 'Madden 26',   lastLogin: '2026-04-10', joined: '2026-02-05' },
  { id: '6', email: 'morgan@example.com',   username: 'MorganFPS',    tier: 'competitive', activeTitle: 'Warzone',     lastLogin: '2026-04-09', joined: '2026-01-11' },
  { id: '7', email: 'riley@example.com',     username: 'RileyDubs',    tier: 'free',        activeTitle: 'Fortnite',    lastLogin: '2026-04-07', joined: '2026-03-01' },
  { id: '8', email: 'drew@example.com',     username: 'DrewChamp',    tier: 'elite',       activeTitle: 'EA FC 26',    lastLogin: '2026-04-12', joined: '2025-10-20' },
  { id: '9', email: 'pat@example.com',       username: 'PatSwing',     tier: 'competitive', activeTitle: 'PGA 2K25',    lastLogin: '2026-04-06', joined: '2026-02-28' },
  { id: '10', email: 'avery@example.com',   username: 'AveryKO',      tier: 'free',        activeTitle: 'UFC 5',       lastLogin: '2026-04-05', joined: '2026-03-15' },
];

const TIER_BADGE: Record<string, string> = {
  free:        'bg-dark-700 text-dark-300',
  competitive: 'bg-blue-500/10 text-blue-400',
  elite:       'bg-forge-400/10 text-forge-400',
  team:        'bg-amber-500/10 text-amber-400',
};

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function AdminUsersPage() {
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState<string>('all');

  const filtered = useMemo(() => {
    return MOCK_USERS.filter((u) => {
      const matchesSearch =
        !search ||
        u.email.toLowerCase().includes(search.toLowerCase()) ||
        u.username.toLowerCase().includes(search.toLowerCase());
      const matchesTier = tierFilter === 'all' || u.tier === tierFilter;
      return matchesSearch && matchesTier;
    });
  }, [search, tierFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Users className="h-6 w-6 text-forge-400" />
        <h1 className="text-2xl font-bold text-dark-50">Users</h1>
        <span className="ml-auto text-sm text-dark-400">
          {filtered.length} user{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-500" />
          <input
            type="text"
            placeholder="Search by email or username..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-dark-700 bg-dark-800 py-2 pl-10 pr-4 text-sm text-dark-100 placeholder-dark-500 focus:border-forge-400 focus:outline-none focus:ring-1 focus:ring-forge-400"
          />
        </div>
        <select
          value={tierFilter}
          onChange={(e) => setTierFilter(e.target.value)}
          className="rounded-lg border border-dark-700 bg-dark-800 px-4 py-2 text-sm text-dark-100 focus:border-forge-400 focus:outline-none focus:ring-1 focus:ring-forge-400"
        >
          <option value="all">All Tiers</option>
          <option value="free">Free</option>
          <option value="competitive">Competitive</option>
          <option value="elite">Elite</option>
          <option value="team">Team</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-dark-700/60 bg-dark-900">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700/60 text-left text-xs text-dark-400">
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Username</th>
              <th className="px-4 py-3 font-medium">Tier</th>
              <th className="px-4 py-3 font-medium">Active Title</th>
              <th className="px-4 py-3 font-medium">Last Login</th>
              <th className="px-4 py-3 font-medium">Joined</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((u) => (
              <tr
                key={u.id}
                className="border-b border-dark-700/30 transition-colors hover:bg-dark-800/40"
              >
                <td className="px-4 py-3 text-dark-100">{u.email}</td>
                <td className="px-4 py-3 font-medium text-dark-100">{u.username}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${TIER_BADGE[u.tier]}`}
                  >
                    {u.tier}
                  </span>
                </td>
                <td className="px-4 py-3 text-dark-300">
                  {u.activeTitle ?? <span className="text-dark-600">None</span>}
                </td>
                <td className="px-4 py-3 text-dark-300">{u.lastLogin}</td>
                <td className="px-4 py-3 text-dark-300">{u.joined}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button
                      title="View Profile"
                      className="rounded p-1.5 text-dark-400 transition-colors hover:bg-dark-700 hover:text-dark-100"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    <button
                      title="Change Tier"
                      className="rounded p-1.5 text-dark-400 transition-colors hover:bg-dark-700 hover:text-dark-100"
                    >
                      <RefreshCw className="h-4 w-4" />
                    </button>
                    <button
                      title="Suspend"
                      className="rounded p-1.5 text-dark-400 transition-colors hover:bg-red-500/10 hover:text-red-400"
                    >
                      <Ban className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-dark-500">
                  No users match your search.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

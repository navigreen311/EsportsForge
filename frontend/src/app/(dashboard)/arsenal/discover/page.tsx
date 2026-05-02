/**
 * Discover New Weapons — Claude web_search powered.
 */

'use client';

import { useState } from 'react';
import { Search as SearchIcon, Loader2, Globe } from 'lucide-react';
import { clsx } from 'clsx';
import api from '@/lib/api';
import { useActiveArsenalTitle } from '@/hooks/useArsenal';
import {
  TITLE_DISPLAY_NAME,
  TITLE_QUICK_SEARCHES,
} from '@/lib/arsenal/titleMeta';
import { WeaponCard } from '@/components/arsenal/WeaponCard';
import { WeaponDetail } from '@/components/arsenal/WeaponDetail';
import type { Weapon } from '@/hooks/useArsenal';

export default function DiscoverPage() {
  const titleId = useActiveArsenalTitle();
  const pills = TITLE_QUICK_SEARCHES[titleId] ?? [];
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Weapon[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);

  const runSearch = async (q: string) => {
    if (!q.trim()) return;
    setQuery(q);
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post<Weapon[]>('/arsenal/discover', {
        query: q,
        title_id: titleId,
      });
      setResults(data);
    } catch (e: unknown) {
      const msg =
        e instanceof Error ? e.message : 'Search failed — try again in a moment.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-3 text-3xl font-bold text-dark-50">
          <Globe className="h-8 w-8 text-forge-400" />
          Discover New Weapons
        </h1>
        <p className="mt-1 text-dark-400">
          ArsenalAI searches the web for trick plays, unstoppable concepts, and
          meta exploits for {TITLE_DISPLAY_NAME[titleId]}
        </p>
      </div>

      {/* Search bar */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') runSearch(query);
            }}
            placeholder={`${TITLE_DISPLAY_NAME[titleId]} unstoppable plays...`}
            className="w-full rounded-lg border border-dark-700 bg-dark-800 py-2 pl-9 pr-3 text-sm text-dark-50 placeholder-dark-500 focus:border-forge-500 focus:outline-none"
          />
        </div>
        <button
          type="button"
          onClick={() => runSearch(query)}
          disabled={loading || !query.trim()}
          className={clsx(
            'rounded-lg bg-forge-500 px-4 py-2 text-sm font-bold text-dark-950 transition-colors hover:bg-forge-400',
            (loading || !query.trim()) && 'cursor-not-allowed opacity-60'
          )}
        >
          Search
        </button>
      </div>

      {/* Quick search pills */}
      {pills.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {pills.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => runSearch(p)}
              className="rounded-full border border-dark-700 bg-dark-800 px-3 py-1 text-[11px] font-medium text-dark-300 hover:border-forge-500/40 hover:text-forge-300"
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Results */}
      {loading && (
        <div className="rounded-xl border border-dark-700 bg-dark-900/60 p-10 text-center text-sm text-dark-400">
          <Loader2 className="mx-auto mb-2 h-6 w-6 animate-spin text-forge-400" />
          ArsenalAI is searching the web for {TITLE_DISPLAY_NAME[titleId]} secret weapons…
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}
      {!loading && !error && results.length > 0 && (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {results.map((w) => (
            <WeaponCard key={w.id} weapon={w} onView={() => setOpenId(w.id)} />
          ))}
        </div>
      )}
      {!loading && !error && results.length === 0 && query && (
        <div className="rounded-xl border border-dark-700 bg-dark-900/60 p-10 text-center text-sm text-dark-400">
          No results yet — try a different phrasing or pick a quick search above.
        </div>
      )}

      <WeaponDetail weaponId={openId} onClose={() => setOpenId(null)} />
    </div>
  );
}

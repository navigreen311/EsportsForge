/**
 * Secret Weapon Arsenal — main library page.
 * Tabs: My Arsenal · All Weapons · Discover New (sub-route) · Upload (sub-route)
 */

'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Zap, Search, X } from 'lucide-react';
import { clsx } from 'clsx';
import {
  useWeapons,
  useMyArsenal,
  useActiveArsenalTitle,
  type WeaponFilters as WF,
} from '@/hooks/useArsenal';
import { WeaponCard } from '@/components/arsenal/WeaponCard';
import { WeaponFilters } from '@/components/arsenal/WeaponFilters';
import { WeaponDetail } from '@/components/arsenal/WeaponDetail';
import { VoiceCommandBar } from '@/components/arsenal/VoiceCommandBar';
import { TITLE_DISPLAY_NAME } from '@/lib/arsenal/titleMeta';

type Tab = 'my' | 'all';

const TAB_LABEL: Record<Tab, string> = {
  my: 'My Arsenal',
  all: 'All Weapons',
};

export default function ArsenalPage() {
  return (
    <Suspense fallback={null}>
      <ArsenalPageInner />
    </Suspense>
  );
}

function ArsenalPageInner() {
  const router = useRouter();
  const titleId = useActiveArsenalTitle();
  const [tab, setTab] = useState<Tab>('all');
  const [filters, setFilters] = useState<WF>({ sort: 'most-recent' });
  const [search, setSearch] = useState('');
  const [openWeaponId, setOpenWeaponId] = useState<string | null>(null);
  const [openInPractice, setOpenInPractice] = useState(false);
  const searchParams = useSearchParams();

  // Deep-link: ?weapon=ID opens the slide-over (used by ArsenalAI alerts).
  useEffect(() => {
    const id = searchParams?.get('weapon');
    if (id) {
      setOpenWeaponId(id);
      setOpenInPractice(searchParams?.get('practice') === '1');
    }
  }, [searchParams]);

  const allQuery = useWeapons({ ...filters, q: search.trim() || undefined });
  const myQuery = useMyArsenal();

  const list = tab === 'my' ? myQuery.data ?? [] : allQuery.data ?? [];
  const isLoading = tab === 'my' ? myQuery.isLoading : allQuery.isLoading;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold text-dark-50">
            <Zap className="h-8 w-8 text-forge-400" />
            Secret Weapon Arsenal
          </h1>
          <p className="mt-1 text-dark-400">
            Trick plays, unstoppable concepts, and secret weapons
          </p>
        </div>

        <div className="inline-flex items-center gap-1 rounded-full border border-forge-500/30 bg-forge-500/5 px-3 py-1.5 text-xs">
          <span className="text-dark-400">Currently showing:</span>
          <span className="font-semibold text-forge-300">
            {TITLE_DISPLAY_NAME[titleId]}
          </span>
        </div>
      </div>

      {/* Voice command bar */}
      <VoiceCommandBar
        onOpenWeapon={(id) => {
          setOpenInPractice(false);
          setOpenWeaponId(id);
        }}
        onPracticeWeapon={(id) => {
          setOpenInPractice(true);
          setOpenWeaponId(id);
        }}
      />

      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto rounded-lg border border-dark-700/50 bg-dark-900/60 p-1">
        {(['my', 'all'] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={clsx(
              'whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium transition-colors',
              tab === t
                ? 'bg-dark-700 text-dark-50 shadow-sm'
                : 'text-dark-400 hover:text-dark-200'
            )}
          >
            {TAB_LABEL[t]}
          </button>
        ))}
        <Link
          href="/arsenal/discover"
          className="whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium text-dark-400 hover:text-dark-200"
        >
          Discover New
        </Link>
        <Link
          href="/arsenal/upload"
          className="whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium text-dark-400 hover:text-dark-200"
        >
          Upload
        </Link>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-500" />
        <input
          type="text"
          placeholder="Search weapons..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-dark-700 bg-dark-800 py-2 pl-9 pr-9 text-sm text-dark-50 placeholder-dark-500 focus:border-forge-500 focus:outline-none"
        />
        {search && (
          <button
            type="button"
            onClick={() => setSearch('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-500 hover:text-dark-300"
            aria-label="Clear search"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Body — sidebar filters + grid */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[220px_1fr]">
        <aside className="hidden lg:block">
          <WeaponFilters titleId={titleId} filters={filters} onChange={setFilters} />
        </aside>

        <div>
          {isLoading ? (
            <p className="rounded-xl border border-dark-700 bg-dark-900/60 p-6 text-center text-sm text-dark-400">
              Loading weapons…
            </p>
          ) : list.length === 0 ? (
            <EmptyState tab={tab} title={TITLE_DISPLAY_NAME[titleId]} router={router} />
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {list.map((w) => (
                <WeaponCard
                  key={w.id}
                  weapon={w}
                  onView={() => setOpenWeaponId(w.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      <WeaponDetail
        weaponId={openWeaponId}
        startInPracticeMode={openInPractice}
        onClose={() => {
          setOpenWeaponId(null);
          setOpenInPractice(false);
        }}
      />
    </div>
  );
}

function EmptyState({
  tab,
  title,
  router,
}: {
  tab: Tab;
  title: string;
  router: ReturnType<typeof useRouter>;
}) {
  if (tab === 'my') {
    return (
      <div className="rounded-xl border border-dark-700 bg-dark-900/60 p-10 text-center">
        <Zap className="mx-auto mb-2 h-10 w-10 text-dark-600" />
        <p className="text-sm font-bold text-dark-100">No weapons saved yet</p>
        <p className="mt-1 text-xs text-dark-400">
          Browse the weapon library or discover new plays to add
        </p>
        <div className="mt-4 inline-flex items-center gap-2">
          <button
            type="button"
            onClick={() => router.push('/arsenal')}
            className="rounded-md border border-dark-700 bg-dark-800 px-3 py-1.5 text-xs font-medium text-dark-200 hover:bg-dark-700"
          >
            Browse All Weapons
          </button>
          <Link
            href="/arsenal/discover"
            className="rounded-md bg-forge-500 px-3 py-1.5 text-xs font-bold text-dark-950 hover:bg-forge-400"
          >
            Discover New
          </Link>
        </div>
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/60 p-10 text-center">
      <p className="text-sm font-bold text-dark-100">
        No weapons yet for {title}
      </p>
      <p className="mt-1 text-xs text-dark-400">
        Be the first to add one
      </p>
      <div className="mt-4 inline-flex items-center gap-2">
        <Link
          href="/arsenal/upload"
          className="rounded-md border border-dark-700 bg-dark-800 px-3 py-1.5 text-xs font-medium text-dark-200 hover:bg-dark-700"
        >
          Upload a Weapon
        </Link>
        <Link
          href="/arsenal/discover"
          className="rounded-md bg-forge-500 px-3 py-1.5 text-xs font-bold text-dark-950 hover:bg-forge-400"
        >
          Discover New
        </Link>
      </div>
    </div>
  );
}

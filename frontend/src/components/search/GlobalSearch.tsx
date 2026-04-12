'use client';

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import {
  Search,
  LayoutDashboard,
  Gamepad2,
  Users,
  Target,
  BarChart3,
  Settings,
  Trophy,
  Lock,
  Swords,
  X,
  Clock,
  FileText,
  Video,
  Image,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Search index                                                       */
/* ------------------------------------------------------------------ */

interface SearchItem {
  id: string;
  category: 'PAGES' | 'OPPONENTS' | 'DRILLS' | 'VAULT';
  title: string;
  subtitle: string;
  icon: LucideIcon;
  href: string;
}

const SEARCH_INDEX: SearchItem[] = [
  // Pages
  { id: 'p-dashboard', category: 'PAGES', title: 'Dashboard', subtitle: 'Overview & stats', icon: LayoutDashboard, href: '/dashboard' },
  { id: 'p-gameplan', category: 'PAGES', title: 'Gameplan', subtitle: 'Strategy builder', icon: Gamepad2, href: '/gameplan' },
  { id: 'p-opponents', category: 'PAGES', title: 'Opponents', subtitle: 'Scouting reports', icon: Users, href: '/opponents' },
  { id: 'p-drills', category: 'PAGES', title: 'Drills', subtitle: 'Practice routines', icon: Target, href: '/drills' },
  { id: 'p-analytics', category: 'PAGES', title: 'Analytics', subtitle: 'Performance data', icon: BarChart3, href: '/analytics' },
  { id: 'p-settings', category: 'PAGES', title: 'Settings', subtitle: 'App preferences', icon: Settings, href: '/settings' },
  { id: 'p-tournament', category: 'PAGES', title: 'Tournament', subtitle: 'Brackets & schedules', icon: Trophy, href: '/tournament' },
  { id: 'p-vault', category: 'PAGES', title: 'Vault', subtitle: 'Secure file storage', icon: Lock, href: '/vault' },
  { id: 'p-warroom', category: 'PAGES', title: 'War Room', subtitle: 'Live match command center', icon: Swords, href: '/warroom' },

  // Sample opponents
  { id: 'o-fnatic', category: 'OPPONENTS', title: 'Fnatic', subtitle: 'EU - Aggressive playstyle', icon: Users, href: '/opponents' },
  { id: 'o-cloud9', category: 'OPPONENTS', title: 'Cloud9', subtitle: 'NA - Adaptive strategies', icon: Users, href: '/opponents' },
  { id: 'o-t1', category: 'OPPONENTS', title: 'T1', subtitle: 'KR - Macro focused', icon: Users, href: '/opponents' },
  { id: 'o-navi', category: 'OPPONENTS', title: 'Natus Vincere', subtitle: 'EU - Star player carry', icon: Users, href: '/opponents' },
  { id: 'o-geng', category: 'OPPONENTS', title: 'Gen.G', subtitle: 'KR - Disciplined rotations', icon: Users, href: '/opponents' },

  // Sample drills
  { id: 'd-aim', category: 'DRILLS', title: 'Aim Training Routine', subtitle: '15 min daily warmup', icon: Target, href: '/drills' },
  { id: 'd-retake', category: 'DRILLS', title: 'Retake Scenarios', subtitle: 'Post-plant situations', icon: Target, href: '/drills' },
  { id: 'd-util', category: 'DRILLS', title: 'Utility Lineups', subtitle: 'Smoke & flash practice', icon: Target, href: '/drills' },
  { id: 'd-eco', category: 'DRILLS', title: 'Eco Round Strats', subtitle: 'Force-buy executes', icon: Target, href: '/drills' },
  { id: 'd-comms', category: 'DRILLS', title: 'Communication Drills', subtitle: 'Callout speed training', icon: Target, href: '/drills' },

  // Sample vault entries
  { id: 'v-scrim1', category: 'VAULT', title: 'Scrim vs Fnatic — Map 1', subtitle: 'VOD review notes', icon: Video, href: '/vault' },
  { id: 'v-strats', category: 'VAULT', title: 'Pistol Round Playbook', subtitle: 'Strategy document', icon: FileText, href: '/vault' },
  { id: 'v-heatmap', category: 'VAULT', title: 'Inferno Heatmap', subtitle: 'Position analysis image', icon: Image, href: '/vault' },
  { id: 'v-demo', category: 'VAULT', title: 'Major Qualifier Demo', subtitle: 'Match recording', icon: Video, href: '/vault' },
];

const CATEGORIES: SearchItem['category'][] = ['PAGES', 'OPPONENTS', 'DRILLS', 'VAULT'];
const MAX_PER_CATEGORY = 3;
const RECENT_KEY = 'esportsforge-recent-searches';

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

interface GlobalSearchProps {
  open: boolean;
  onClose: () => void;
}

export function GlobalSearch({ open, onClose }: GlobalSearchProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState('');
  const [highlightIndex, setHighlightIndex] = useState(0);
  const [recentSearches, setRecentSearches] = useState<SearchItem[]>([]);

  // Load recent searches from localStorage
  useEffect(() => {
    if (open) {
      try {
        const stored = localStorage.getItem(RECENT_KEY);
        if (stored) setRecentSearches(JSON.parse(stored));
      } catch {
        /* ignore */
      }
      setQuery('');
      setHighlightIndex(0);
      // Focus input after mount
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Filter results with simple case-insensitive substring matching
  const results = useMemo(() => {
    if (!query.trim()) return [];
    const term = query.toLowerCase();
    const grouped: SearchItem[] = [];

    for (const cat of CATEGORIES) {
      const matches = SEARCH_INDEX.filter(
        (item) =>
          item.category === cat &&
          (item.title.toLowerCase().includes(term) ||
            item.subtitle.toLowerCase().includes(term))
      ).slice(0, MAX_PER_CATEGORY);
      grouped.push(...matches);
    }
    return grouped;
  }, [query]);

  // Items to display: results or recent searches
  const displayItems = query.trim() ? results : recentSearches.slice(0, 5);

  // Reset highlight when results change
  useEffect(() => {
    setHighlightIndex(0);
  }, [query]);

  // Save to recent searches
  const saveRecent = useCallback((item: SearchItem) => {
    setRecentSearches((prev) => {
      const filtered = prev.filter((r) => r.id !== item.id);
      const updated = [item, ...filtered].slice(0, 5);
      try {
        localStorage.setItem(RECENT_KEY, JSON.stringify(updated));
      } catch {
        /* ignore */
      }
      return updated;
    });
  }, []);

  // Navigate to result
  const selectItem = useCallback(
    (item: SearchItem) => {
      saveRecent(item);
      onClose();
      router.push(item.href);
    },
    [saveRecent, onClose, router]
  );

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setHighlightIndex((i) => (i + 1) % Math.max(displayItems.length, 1));
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setHighlightIndex((i) => (i - 1 + displayItems.length) % Math.max(displayItems.length, 1));
        return;
      }
      if (e.key === 'Enter' && displayItems[highlightIndex]) {
        e.preventDefault();
        selectItem(displayItems[highlightIndex]);
      }
    },
    [displayItems, highlightIndex, onClose, selectItem]
  );

  if (!open) return null;

  // Group display items by category for rendering
  const grouped = CATEGORIES.map((cat) => ({
    category: cat,
    items: displayItems.filter((item) => item.category === cat),
  })).filter((g) => g.items.length > 0);

  // Flat index helper
  let flatIdx = -1;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-dark-900/80 backdrop-blur-sm pt-[15vh]"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-xl border border-dark-700/50 bg-dark-800 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 border-b border-dark-700/50 px-4 py-3">
          <Search className="h-5 w-5 shrink-0 text-dark-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search EsportsForge..."
            className="flex-1 bg-transparent text-sm text-dark-100 placeholder:text-dark-500 outline-none"
          />
          <button
            onClick={onClose}
            className="rounded p-1 text-dark-500 hover:bg-dark-700 hover:text-dark-300 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto p-2">
          {displayItems.length === 0 && (
            <p className="px-3 py-8 text-center text-sm text-dark-500">
              {query.trim() ? 'No results found.' : 'Start typing to search...'}
            </p>
          )}

          {!query.trim() && displayItems.length > 0 && (
            <p className="px-3 pt-1 pb-2 text-xs font-semibold uppercase tracking-wider text-dark-500">
              Recent Searches
            </p>
          )}

          {query.trim()
            ? grouped.map((group) => (
                <div key={group.category} className="mb-1">
                  <p className="px-3 pt-2 pb-1 text-xs font-semibold uppercase tracking-wider text-dark-500">
                    {group.category}
                  </p>
                  {group.items.map((item) => {
                    flatIdx++;
                    const idx = flatIdx;
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.id}
                        onClick={() => selectItem(item)}
                        onMouseEnter={() => setHighlightIndex(idx)}
                        className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors ${
                          highlightIndex === idx
                            ? 'bg-dark-700 text-dark-100'
                            : 'text-dark-300 hover:bg-dark-700/50'
                        }`}
                      >
                        <Icon className="h-4 w-4 shrink-0 text-dark-400" />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium">{item.title}</p>
                          <p className="truncate text-xs text-dark-500">{item.subtitle}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              ))
            : displayItems.map((item) => {
                flatIdx++;
                const idx = flatIdx;
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => selectItem(item)}
                    onMouseEnter={() => setHighlightIndex(idx)}
                    className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors ${
                      highlightIndex === idx
                        ? 'bg-dark-700 text-dark-100'
                        : 'text-dark-300 hover:bg-dark-700/50'
                    }`}
                  >
                    <Clock className="h-4 w-4 shrink-0 text-dark-400" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{item.title}</p>
                      <p className="truncate text-xs text-dark-500">{item.subtitle}</p>
                    </div>
                  </button>
                );
              })}
        </div>

        {/* Footer hints */}
        <div className="flex items-center gap-4 border-t border-dark-700/50 px-4 py-2 text-xs text-dark-500">
          <span><kbd className="rounded bg-dark-700 px-1.5 py-0.5 font-mono text-dark-400">↑↓</kbd> navigate</span>
          <span><kbd className="rounded bg-dark-700 px-1.5 py-0.5 font-mono text-dark-400">↵</kbd> select</span>
          <span><kbd className="rounded bg-dark-700 px-1.5 py-0.5 font-mono text-dark-400">esc</kbd> close</span>
        </div>
      </div>
    </div>
  );
}

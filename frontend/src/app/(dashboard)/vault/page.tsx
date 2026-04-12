/**
 * ForgeVault — Searchable Knowledge Base.
 * Full-text search across all competitive intelligence entries with
 * category filters, pinning, and expandable detail panels.
 */

'use client';

import { useState, useMemo, useRef, useEffect } from 'react';
import {
  Search,
  Archive,
  Pin,
  PinOff,
  ChevronDown,
  ChevronUp,
  Calendar,
  Tag,
  X,
  Sparkles,
} from 'lucide-react';
import { clsx } from 'clsx';

// ---------- Types ----------

type VaultCategory =
  | 'Coverage Counter'
  | 'Kill Sheet'
  | 'Loss Pattern'
  | 'Meta Counter'
  | 'Drill Result'
  | 'Gameplan';

interface VaultEntry {
  id: string;
  title: string;
  category: VaultCategory;
  opponent?: string;
  date: string;
  snippet: string;
  content: string;
  confidence: number;
  relatedIds: string[];
  pinned: boolean;
}

// ---------- Mock Data ----------

const MOCK_ENTRIES: VaultEntry[] = [
  {
    id: '1',
    title: 'Cover 3 Sky Beater — Corner Route + Flat',
    category: 'Coverage Counter',
    opponent: 'xKillSwitch',
    date: '2026-04-08',
    snippet: 'Corner route to the boundary with flat combo destroys Cover 3 Sky every time...',
    content: 'Corner route to the boundary with flat combo destroys Cover 3 Sky every time. The cloud flat defender gets pulled down by the flat route, leaving the corner wide open for 20+ yards. Works best from Trips TE formation. Key read: if the flat defender sinks, hit the flat. If he jumps flat, throw corner. 8/10 completions in last 3 sessions against Cover 3 Sky users.',
    confidence: 94,
    relatedIds: ['3', '7'],
    pinned: true,
  },
  {
    id: '2',
    title: 'xKillSwitch Blitz Tendency — 3rd and Long',
    category: 'Kill Sheet',
    opponent: 'xKillSwitch',
    date: '2026-04-07',
    snippet: 'On 3rd and 7+, xKillSwitch sends DB blitz 72% of the time from nickel...',
    content: 'On 3rd and 7+, xKillSwitch sends DB blitz 72% of the time from nickel formation. The nickel corner comes off the slot side. Quick slant to the slot receiver is money — 6/8 conversions. If he drops into zone instead, look for the TE seam. Key tell: if his safety creeps down pre-snap, blitz is coming.',
    confidence: 88,
    relatedIds: ['1', '5'],
    pinned: true,
  },
  {
    id: '3',
    title: 'Cover 2 Man Beater — Mesh Concept',
    category: 'Coverage Counter',
    opponent: undefined,
    date: '2026-04-06',
    snippet: 'Mesh crossing routes with a wheel create natural picks in Cover 2 Man...',
    content: 'Mesh crossing routes with a wheel create natural picks in Cover 2 Man. The LBs get caught in traffic from the mesh, and the wheel is almost always open against Cover 2 Man if you let it develop. Throw timing: when the wheel clears the LB zone. Works from Bunch and Trips formations.',
    confidence: 91,
    relatedIds: ['1'],
    pinned: false,
  },
  {
    id: '4',
    title: 'Loss Pattern: Forcing Deep Shots on 2nd Down',
    category: 'Loss Pattern',
    opponent: 'TTG_Sniper',
    date: '2026-04-05',
    snippet: 'Lost 3 games this week by forcing deep shots on 2nd and medium...',
    content: 'Lost 3 games this week by forcing deep shots on 2nd and medium (2nd and 4-6). Converting short on 2nd and medium keeps drives alive — switched to quick outs and curls, went 4-0 after adjustment. Deep shots on 2nd down had only 23% completion rate vs 71% for short/intermediate.',
    confidence: 85,
    relatedIds: ['9'],
    pinned: false,
  },
  {
    id: '5',
    title: 'xKillSwitch Red Zone Tendencies',
    category: 'Kill Sheet',
    opponent: 'xKillSwitch',
    date: '2026-04-04',
    snippet: 'Inside the 10: 80% Cover 1 Robber. The robber sits in the middle...',
    content: 'Inside the 10: 80% Cover 1 Robber. The robber sits in the middle of the field. Fade + out combo to the boundary beats this consistently. The fade holds the corner and the out gets underneath. Also: PA rollout right with TE drag is 4/4 TDs against this look.',
    confidence: 92,
    relatedIds: ['2'],
    pinned: false,
  },
  {
    id: '6',
    title: 'Meta Counter: Aggressive Man Press',
    category: 'Meta Counter',
    opponent: undefined,
    date: '2026-04-03',
    snippet: 'Current meta is aggressive man press with edge blitz. Motion snap beats press...',
    content: 'Current meta is aggressive man press with edge blitz. Motion snap beats press alignment by forcing late adjustments. Jet motion into quick pass (slant/screen) averages 8.2 YPC against press-heavy users. Also: delayed crossers beat aggressive man when the rush gets home — QB needs 2.5s in pocket.',
    confidence: 89,
    relatedIds: ['3', '8'],
    pinned: false,
  },
  {
    id: '7',
    title: 'Cover 4 Palms Exploiter — Deep In + Drag',
    category: 'Coverage Counter',
    opponent: 'WarMachine99',
    date: '2026-04-02',
    snippet: 'Deep in route at 18 yards paired with a drag underneath consistently beats Cover 4...',
    content: 'Deep in route at 18 yards paired with a drag underneath consistently beats Cover 4 Palms. The match rules in Palms leave the deep in uncovered when paired with a vertical route on the same side. The safety locks the vertical, leaving the deep in wide open in the window. 9/11 completions, avg 16.3 yards.',
    confidence: 93,
    relatedIds: ['1', '3'],
    pinned: false,
  },
  {
    id: '8',
    title: 'Drill Result: Pocket Movement Under Pressure',
    category: 'Drill Result',
    opponent: undefined,
    date: '2026-04-01',
    snippet: 'Completed pocket movement drill — improved escape rate from 34% to 61%...',
    content: 'Completed pocket movement drill — improved escape rate from 34% to 61% over 5 sessions. Key improvements: side-stepping interior rush (up from 28% to 55%), throwing on the move accuracy (up from 41% to 58%). Still need work: throwing left while moving right (32% accuracy). Next session: focus on off-platform throws.',
    confidence: 78,
    relatedIds: ['6'],
    pinned: false,
  },
  {
    id: '9',
    title: 'Gameplan: Conservative 2nd Down Package',
    category: 'Gameplan',
    opponent: undefined,
    date: '2026-03-30',
    snippet: 'New 2nd down package prioritizing high-percentage throws and run game...',
    content: 'New 2nd down package prioritizing high-percentage throws and run game. Core plays: Inside Zone, Power, Quick Out, Curl Flat, HB Screen. Only go deep on 2nd and 2 or less. This package improved 3rd down conversion from 38% to 54% by keeping distances manageable. Key principle: make 3rd down easy, not 2nd down heroic.',
    confidence: 87,
    relatedIds: ['4'],
    pinned: false,
  },
  {
    id: '10',
    title: 'TTG_Sniper Pressure Scheme Breakdown',
    category: 'Kill Sheet',
    opponent: 'TTG_Sniper',
    date: '2026-03-28',
    snippet: 'TTG_Sniper runs overload blitz left 65% of the time. Slide protect right...',
    content: 'TTG_Sniper runs overload blitz left 65% of the time. Slide protect right and ID the mike to the overload side. Hot route the RB to block left. Quick game to the right side of the field is money — slant, out, quick curl all work. He rarely adjusts mid-game; once you establish the slide, he keeps sending it.',
    confidence: 90,
    relatedIds: ['4', '8'],
    pinned: false,
  },
  {
    id: '11',
    title: 'Loss Pattern: Abandoning Run Game After INT',
    category: 'Loss Pattern',
    opponent: undefined,
    date: '2026-03-27',
    snippet: 'After throwing a pick, went pass-only for 3+ drives in 4 different losses...',
    content: 'After throwing a pick, went pass-only for 3+ drives in 4 different losses this month. The run game was working in all 4 games before the INT. Tilt response: "need to make up points fast." Fix: after any turnover, run on 1st down of next drive no matter what. Implemented run-first-after-TO rule, went 3-1 since.',
    confidence: 83,
    relatedIds: ['4', '9'],
    pinned: false,
  },
  {
    id: '12',
    title: 'Meta Counter: Contain Rush Adjustments',
    category: 'Meta Counter',
    opponent: undefined,
    date: '2026-03-25',
    snippet: 'Contain rush is gaining popularity. Counter: designed QB runs up the middle...',
    content: 'Contain rush is gaining popularity. Counter: designed QB runs up the middle when contain is set exploit the vacated A-gaps. Draw plays and QB sneaks average 6.8 YPC against contain. Also: play action is deadly because the ends are sitting wide — PA boot to the contain side gets easy TEs in the flat.',
    confidence: 86,
    relatedIds: ['6'],
    pinned: false,
  },
  {
    id: '13',
    title: 'Drill Result: Route Combo Timing',
    category: 'Drill Result',
    opponent: undefined,
    date: '2026-03-23',
    snippet: 'Route combo timing drill — hitting the correct receiver in 3-read progressions...',
    content: 'Route combo timing drill — hitting the correct receiver in 3-read progressions within 2.8 seconds. Before: 45% correct reads in time. After 8 sessions: 72% correct reads in time. Biggest improvement: identifying cover 2 vs cover 4 pre-snap (was 50/50 guessing, now 80% correct). Still struggling with man/zone blend reads.',
    confidence: 76,
    relatedIds: ['8'],
    pinned: false,
  },
  {
    id: '14',
    title: 'WarMachine99 — Defensive Adjustments Scouting',
    category: 'Kill Sheet',
    opponent: 'WarMachine99',
    date: '2026-03-21',
    snippet: 'WarMachine99 adjusts defense after 2 consecutive completions to same side...',
    content: 'WarMachine99 adjusts defense after 2 consecutive completions to same side. Pattern: hit right side twice, he flips coverage to overplay right on 3rd play. Counter: establish right side early, then attack left on the 3rd play. Also predictable in hurry-up — defaults to Cover 3 when rushed, rarely audibles in no-huddle.',
    confidence: 91,
    relatedIds: ['7'],
    pinned: false,
  },
  {
    id: '15',
    title: 'Gameplan: Anti-Meta Tournament Build',
    category: 'Gameplan',
    opponent: undefined,
    date: '2026-03-19',
    snippet: 'Tournament prep: anti-meta package focused on motion-heavy attack...',
    content: 'Tournament prep: anti-meta package focused on motion-heavy attack and zone-run scheme to counter aggressive man press meta. Core concepts: jet sweep motion (forces press bail), outside zone (attacks over-pursuit from blitz), RPOs (exploit LBs vacating zones). Practice schedule: 3 sessions on motion timing, 2 on zone blocking adjustments.',
    confidence: 84,
    relatedIds: ['6', '9', '12'],
    pinned: false,
  },
  {
    id: '16',
    title: 'Cover 6 Exploit — Flood to the Quarter Side',
    category: 'Coverage Counter',
    opponent: 'DaBot_X',
    date: '2026-03-17',
    snippet: 'Flood concept to the Cover 4 quarter side creates 3-on-2 advantage...',
    content: 'Flood concept to the Cover 4 quarter side creates 3-on-2 advantage against Cover 6. The corner and safety on the quarter side play 2-read match — sending 3 vertical threats overloads them. Best result: streak + corner + flat to quarter side, read the corner defender. If he sinks on the flat, throw the corner. 7/9 completions for 14.2 avg.',
    confidence: 90,
    relatedIds: ['1', '7'],
    pinned: false,
  },
  {
    id: '17',
    title: 'Loss Pattern: Ignoring Field Position',
    category: 'Loss Pattern',
    opponent: undefined,
    date: '2026-03-15',
    snippet: 'Review shows 5 turnovers in own territory from aggressive calls on 1st down...',
    content: 'Review shows 5 turnovers in own territory from aggressive calls on 1st down inside own 30. Risk/reward is terrible here — INT or fumble gives opponent easy points. New rule: inside own 30, 1st down is always a run or quick safe pass. No deep shots until past the 35. Since implementing: 0 turnovers in own territory over 8 games.',
    confidence: 88,
    relatedIds: ['4', '11'],
    pinned: false,
  },
  {
    id: '18',
    title: 'Drill Result: Pre-Snap Coverage ID Speed',
    category: 'Drill Result',
    opponent: undefined,
    date: '2026-03-13',
    snippet: 'Pre-snap coverage identification speed drill — goal: ID within 3 seconds...',
    content: 'Pre-snap coverage identification speed drill — goal: ID within 3 seconds of formation set. Before: 4.1s average, 62% accuracy. After 6 sessions: 2.4s average, 81% accuracy. Key breakthrough: learned to read safety alignment first (deep/shallow), then LB depth as secondary tell. Cover 2 vs Cover 4 now instant. Still slow on disguised single-high.',
    confidence: 80,
    relatedIds: ['13', '8'],
    pinned: false,
  },
];

const CATEGORIES: VaultCategory[] = [
  'Coverage Counter',
  'Kill Sheet',
  'Loss Pattern',
  'Meta Counter',
  'Drill Result',
  'Gameplan',
];

const QUICK_SEARCHES = [
  'Cover 3 counters',
  'vs Blitz Heavy',
  'Red zone plays',
  'Loss patterns',
  'Kill sheet',
  'Meta counters',
  'Drill results',
];

const CATEGORY_COLORS: Record<VaultCategory, string> = {
  'Coverage Counter': 'bg-blue-500/15 text-blue-400',
  'Kill Sheet': 'bg-red-500/15 text-red-400',
  'Loss Pattern': 'bg-amber-500/15 text-amber-400',
  'Meta Counter': 'bg-purple-500/15 text-purple-400',
  'Drill Result': 'bg-teal-500/15 text-teal-400',
  'Gameplan': 'bg-forge-500/15 text-forge-400',
};

// ---------- Component ----------

export default function VaultPage() {
  const [entries, setEntries] = useState<VaultEntry[]>(MOCK_ENTRIES);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<VaultCategory | null>(null);
  const [selectedOpponent, setSelectedOpponent] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    searchRef.current?.focus();
  }, []);

  const opponents = useMemo(() => {
    const ops = new Set<string>();
    entries.forEach((e) => { if (e.opponent) ops.add(e.opponent); });
    return Array.from(ops).sort();
  }, [entries]);

  const filteredEntries = useMemo(() => {
    let results = [...entries];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      results = results.filter(
        (e) =>
          e.title.toLowerCase().includes(q) ||
          e.snippet.toLowerCase().includes(q) ||
          e.content.toLowerCase().includes(q) ||
          e.category.toLowerCase().includes(q) ||
          (e.opponent && e.opponent.toLowerCase().includes(q))
      );
    }

    if (selectedCategory) {
      results = results.filter((e) => e.category === selectedCategory);
    }

    if (selectedOpponent) {
      results = results.filter((e) => e.opponent === selectedOpponent);
    }

    if (dateFrom) {
      results = results.filter((e) => e.date >= dateFrom);
    }
    if (dateTo) {
      results = results.filter((e) => e.date <= dateTo);
    }

    // Pinned first, then by date desc
    results.sort((a, b) => {
      if (a.pinned && !b.pinned) return -1;
      if (!a.pinned && b.pinned) return 1;
      return b.date.localeCompare(a.date);
    });

    return results;
  }, [entries, searchQuery, selectedCategory, selectedOpponent, dateFrom, dateTo]);

  const togglePin = (id: string) => {
    setEntries((prev) =>
      prev.map((e) => (e.id === id ? { ...e, pinned: !e.pinned } : e))
    );
  };

  const applyQuickSearch = (query: string) => {
    setSearchQuery(query);
    setSelectedCategory(null);
    setSelectedOpponent(null);
    setDateFrom('');
    setDateTo('');
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedCategory(null);
    setSelectedOpponent(null);
    setDateFrom('');
    setDateTo('');
  };

  const hasActiveFilters = searchQuery || selectedCategory || selectedOpponent || dateFrom || dateTo;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold text-dark-50">
            <Archive className="h-8 w-8 text-forge-400" />
            ForgeVault
          </h1>
          <p className="mt-1 text-dark-400">
            Your competitive knowledge base — search, filter, and pin intel.
          </p>
        </div>
        <div className="text-sm text-dark-500">
          {entries.length} entries | {entries.filter((e) => e.pinned).length} pinned
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-dark-500" />
        <input
          ref={searchRef}
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search entries by title, content, opponent, category..."
          className="w-full rounded-xl border border-dark-700/50 bg-dark-900 py-3.5 pl-12 pr-12 text-dark-100 placeholder-dark-500 transition-colors focus:border-forge-500/50 focus:outline-none focus:ring-1 focus:ring-forge-500/30"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-dark-500 hover:text-dark-300"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Quick Searches */}
      <div className="flex flex-wrap gap-2">
        <span className="flex items-center gap-1.5 text-xs font-medium text-dark-500">
          <Sparkles className="h-3.5 w-3.5" /> Quick:
        </span>
        {QUICK_SEARCHES.map((q) => (
          <button
            key={q}
            onClick={() => applyQuickSearch(q)}
            className={clsx(
              'rounded-full px-3 py-1 text-xs font-medium transition-colors',
              searchQuery === q
                ? 'bg-forge-500/20 text-forge-400'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700 hover:text-dark-200'
            )}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Filters Toggle */}
      <div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 text-sm font-medium text-dark-400 hover:text-dark-200"
        >
          <Tag className="h-4 w-4" />
          Filters
          {showFilters ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          {hasActiveFilters && (
            <span className="ml-1 rounded-full bg-forge-500/20 px-2 py-0.5 text-[10px] text-forge-400">
              Active
            </span>
          )}
        </button>

        {showFilters && (
          <div className="mt-3 grid grid-cols-1 gap-3 rounded-xl border border-dark-700/50 bg-dark-900/50 p-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Category */}
            <div>
              <label className="mb-1 block text-xs font-medium text-dark-400">Category</label>
              <select
                value={selectedCategory ?? ''}
                onChange={(e) => setSelectedCategory(e.target.value as VaultCategory || null)}
                className="w-full rounded-lg border border-dark-700/50 bg-dark-800 px-3 py-2 text-sm text-dark-200 focus:border-forge-500/50 focus:outline-none"
              >
                <option value="">All Categories</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            {/* Opponent */}
            <div>
              <label className="mb-1 block text-xs font-medium text-dark-400">Opponent</label>
              <select
                value={selectedOpponent ?? ''}
                onChange={(e) => setSelectedOpponent(e.target.value || null)}
                className="w-full rounded-lg border border-dark-700/50 bg-dark-800 px-3 py-2 text-sm text-dark-200 focus:border-forge-500/50 focus:outline-none"
              >
                <option value="">All Opponents</option>
                {opponents.map((o) => (
                  <option key={o} value={o}>{o}</option>
                ))}
              </select>
            </div>

            {/* Date From */}
            <div>
              <label className="mb-1 block text-xs font-medium text-dark-400">From</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-full rounded-lg border border-dark-700/50 bg-dark-800 px-3 py-2 text-sm text-dark-200 focus:border-forge-500/50 focus:outline-none"
              />
            </div>

            {/* Date To */}
            <div>
              <label className="mb-1 block text-xs font-medium text-dark-400">To</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-full rounded-lg border border-dark-700/50 bg-dark-800 px-3 py-2 text-sm text-dark-200 focus:border-forge-500/50 focus:outline-none"
              />
            </div>

            {/* Clear */}
            {hasActiveFilters && (
              <div className="flex items-end sm:col-span-2 lg:col-span-4">
                <button
                  onClick={clearFilters}
                  className="text-xs font-medium text-dark-500 hover:text-red-400"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Results Count */}
      <div className="text-sm text-dark-500">
        {filteredEntries.length} result{filteredEntries.length !== 1 ? 's' : ''}
        {!hasActiveFilters && ' (recent entries)'}
      </div>

      {/* Results Grid */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {filteredEntries.map((entry) => {
          const isExpanded = expandedId === entry.id;
          const relatedEntries = entries.filter((e) => entry.relatedIds.includes(e.id));

          return (
            <div
              key={entry.id}
              className={clsx(
                'rounded-xl border transition-all duration-200',
                entry.pinned
                  ? 'border-forge-500/30 bg-dark-900/80'
                  : 'border-dark-700/50 bg-dark-900/50',
                isExpanded && 'lg:col-span-2'
              )}
            >
              {/* Card Header */}
              <div className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <span className={clsx('rounded-full px-2.5 py-0.5 text-[11px] font-medium', CATEGORY_COLORS[entry.category])}>
                        {entry.category}
                      </span>
                      {entry.opponent && (
                        <span className="rounded-full bg-dark-800 px-2.5 py-0.5 text-[11px] font-medium text-dark-300">
                          vs {entry.opponent}
                        </span>
                      )}
                      {entry.pinned && (
                        <Pin className="h-3 w-3 text-forge-400" />
                      )}
                    </div>
                    <h3 className="text-sm font-semibold text-dark-100">{entry.title}</h3>
                    <p className="mt-1 text-xs text-dark-400 line-clamp-2">{entry.snippet}</p>
                  </div>

                  {/* Confidence Score */}
                  <div className="flex flex-col items-center gap-1">
                    <div
                      className={clsx(
                        'flex h-10 w-10 items-center justify-center rounded-lg text-xs font-bold',
                        entry.confidence >= 90
                          ? 'bg-forge-500/15 text-forge-400'
                          : entry.confidence >= 80
                          ? 'bg-blue-500/15 text-blue-400'
                          : 'bg-dark-800 text-dark-300'
                      )}
                    >
                      {entry.confidence}%
                    </div>
                  </div>
                </div>

                {/* Footer row */}
                <div className="mt-3 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-[11px] text-dark-500">
                    <Calendar className="h-3 w-3" />
                    <span>{entry.date}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => togglePin(entry.id)}
                      className={clsx(
                        'rounded-lg p-1.5 transition-colors',
                        entry.pinned
                          ? 'text-forge-400 hover:text-forge-300'
                          : 'text-dark-600 hover:text-dark-300'
                      )}
                      title={entry.pinned ? 'Unpin' : 'Pin'}
                    >
                      {entry.pinned ? <PinOff className="h-3.5 w-3.5" /> : <Pin className="h-3.5 w-3.5" />}
                    </button>
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : entry.id)}
                      className="rounded-lg p-1.5 text-dark-600 transition-colors hover:text-dark-300"
                    >
                      {isExpanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                    </button>
                  </div>
                </div>
              </div>

              {/* Expanded Detail */}
              {isExpanded && (
                <div className="border-t border-dark-700/50 p-4">
                  <p className="text-sm leading-relaxed text-dark-200">{entry.content}</p>

                  {relatedEntries.length > 0 && (
                    <div className="mt-4">
                      <h4 className="mb-2 text-xs font-medium text-dark-400">Related Entries</h4>
                      <div className="flex flex-wrap gap-2">
                        {relatedEntries.map((related) => (
                          <button
                            key={related.id}
                            onClick={() => setExpandedId(related.id)}
                            className="rounded-lg bg-dark-800 px-3 py-1.5 text-xs text-dark-300 transition-colors hover:bg-dark-700 hover:text-dark-100"
                          >
                            {related.title.substring(0, 40)}...
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Empty state */}
      {filteredEntries.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dark-700/50 bg-dark-900/50 py-16">
          <Archive className="mb-3 h-10 w-10 text-dark-600" />
          <p className="text-sm font-medium text-dark-400">No entries match your search.</p>
          <button
            onClick={clearFilters}
            className="mt-2 text-xs text-forge-400 hover:text-forge-300"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
}

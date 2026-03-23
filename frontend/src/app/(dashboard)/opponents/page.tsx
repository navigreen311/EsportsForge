'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useOpponents } from '@/hooks/useOpponents';
import OpponentCard from '@/components/opponents/OpponentCard';
import { OpponentFilter, OpponentSort, Opponent } from '@/types/opponent';
import { calculateThreatLevel } from '@/components/opponents/ThreatLevelBadge';
import {
  Search,
  Users,
  Swords,
  Clock,
  Eye,
  ArrowUpDown,
  UserPlus,
} from 'lucide-react';

const filters: { key: OpponentFilter; label: string; icon: React.ReactNode }[] = [
  { key: 'all', label: 'All', icon: <Users className="w-4 h-4" /> },
  { key: 'rivals', label: 'Rivals', icon: <Swords className="w-4 h-4" /> },
  { key: 'recent', label: 'Recent', icon: <Clock className="w-4 h-4" /> },
  { key: 'scouted', label: 'Scouted', icon: <Eye className="w-4 h-4" /> },
];

const sorts: { key: OpponentSort | 'threatLevel'; label: string }[] = [
  { key: 'threatLevel', label: 'Threat Level' },
  { key: 'lastSeen', label: 'Last Seen' },
  { key: 'encounters', label: 'Encounters' },
  { key: 'winRate', label: 'Win Rate vs' },
];

export default function OpponentsPage() {
  const router = useRouter();
  const {
    opponents,
    search,
    setSearch,
    filter,
    setFilter,
    sort,
    setSort,
  } = useOpponents();
  const [localSort, setLocalSort] = useState<string>('threatLevel');

  const handleSortChange = (key: string) => {
    setLocalSort(key);
    if (key !== 'threatLevel') {
      setSort(key as OpponentSort);
    }
  };

  // Apply threat level sort locally
  const sortedOpponents = localSort === 'threatLevel'
    ? [...opponents].sort((a, b) => calculateThreatLevel(b) - calculateThreatLevel(a))
    : opponents;

  const handleOpponentClick = (opponent: Opponent) => {
    router.push(`/opponents/${opponent.id}`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-dark-50 flex items-center gap-3">
            <Users className="w-8 h-8 text-forge-400" />
            Opponents
          </h1>
          <p className="text-dark-400 mt-1">
            Scout, analyze, and track your competition
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-forge-500 hover:bg-forge-600 text-white font-medium text-sm transition-colors shadow-lg shadow-forge-500/20">
          <UserPlus className="w-4 h-4" />
          Scout New Opponent
        </button>
      </div>

      {/* Search + Filters + Sort */}
      <div className="space-y-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by gamertag..."
            className="w-full pl-10 pr-4 py-3 rounded-xl bg-dark-900/50 border border-dark-700 text-dark-100 placeholder-dark-500 focus:outline-none focus:border-dark-500 focus:ring-1 focus:ring-dark-500 transition-colors text-sm"
          />
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          {/* Filter Tabs */}
          <div className="flex gap-1 p-1 rounded-lg bg-dark-900/50 border border-dark-700">
            {filters.map((f) => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-xs font-medium transition-all ${
                  filter === f.key
                    ? 'bg-dark-700 text-dark-50 shadow-sm'
                    : 'text-dark-400 hover:text-dark-200 hover:bg-dark-800/50'
                }`}
              >
                {f.icon}
                {f.label}
              </button>
            ))}
          </div>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-dark-500" />
            <select
              value={localSort}
              onChange={(e) => handleSortChange(e.target.value)}
              className="bg-dark-900/50 border border-dark-700 text-dark-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-dark-500 cursor-pointer"
            >
              {sorts.map((s) => (
                <option key={s.key} value={s.key}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          {/* Result Count */}
          <span className="text-xs text-dark-500 sm:ml-auto">
            {sortedOpponents.length} opponent{sortedOpponents.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Opponent Card Grid */}
      {sortedOpponents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedOpponents.map((opponent) => (
            <OpponentCard
              key={opponent.id}
              opponent={opponent}
              onClick={handleOpponentClick}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-16 rounded-xl border border-dark-700 bg-dark-900/50">
          <Users className="w-12 h-12 text-dark-600 mx-auto mb-3" />
          <p className="text-dark-400 font-medium">No opponents found</p>
          <p className="text-dark-500 text-sm mt-1">
            {search
              ? 'Try adjusting your search terms'
              : 'Scout your first opponent to get started'}
          </p>
        </div>
      )}
    </div>
  );
}

'use client';

import { useState } from 'react';
import {
  Trophy,
  Medal,
  TrendingUp,
  Filter,
  Info,
  ChevronDown,
  Crown,
  Target,
  Zap,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface LeaderboardEntry {
  rank: number;
  gamertag: string;
  title: string;
  winRate: number;
  percentile: number;
}

// ---------------------------------------------------------------------------
// Mock Data
// ---------------------------------------------------------------------------

const MOCK_PLAYERS: LeaderboardEntry[] = [
  { rank: 1, gamertag: 'xShadowKing', title: 'Madden 26', winRate: 92.3, percentile: 99 },
  { rank: 2, gamertag: 'ProGrinder99', title: 'Madden 26', winRate: 89.7, percentile: 98 },
  { rank: 3, gamertag: 'ClutchMaster', title: 'Madden 26', winRate: 87.1, percentile: 97 },
  { rank: 4, gamertag: 'GridironAce', title: 'Madden 26', winRate: 85.4, percentile: 96 },
  { rank: 5, gamertag: 'BlitzKingX', title: 'Madden 26', winRate: 83.9, percentile: 95 },
  { rank: 6, gamertag: 'TDmachine22', title: 'Madden 26', winRate: 81.2, percentile: 93 },
  { rank: 7, gamertag: 'PocketSniper', title: 'Madden 26', winRate: 79.8, percentile: 91 },
  { rank: 8, gamertag: 'ZoneBuster', title: 'Madden 26', winRate: 78.3, percentile: 89 },
  { rank: 9, gamertag: 'EndZoneElite', title: 'Madden 26', winRate: 76.5, percentile: 87 },
  { rank: 10, gamertag: 'ForgeLegend', title: 'Madden 26', winRate: 74.9, percentile: 85 },
];

const TITLES = ['All Titles', 'Madden 26', 'CFB 26', 'NBA 2K26', 'EA FC 26'];
const TIERS = ['All Tiers', 'Elite', 'Pro', 'Competitor', 'Rising'];
const SKILLS = ['Overall', 'Offense', 'Defense', 'Clutch', 'Adaptability'];
const TIMEFRAMES = ['Weekly', 'Monthly', 'All Time'];
const TABS = ['By Title', 'By Skill', 'Weekly Movers'] as const;

type Tab = (typeof TABS)[number];

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) return <Crown className="h-5 w-5 text-yellow-400" />;
  if (rank === 2) return <Medal className="h-5 w-5 text-gray-300" />;
  if (rank === 3) return <Medal className="h-5 w-5 text-amber-600" />;
  return <span className="text-sm font-mono text-zinc-400">#{rank}</span>;
}

function FilterDropdown({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: string[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="relative">
      <label className="block text-xs text-zinc-500 mb-1">{label}</label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="appearance-none w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 pr-8 text-sm text-zinc-200 focus:outline-none focus:ring-2 focus:ring-green-500/40"
        >
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500 pointer-events-none" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function LeaderboardPage() {
  const [activeTab, setActiveTab] = useState<Tab>('By Title');
  const [titleFilter, setTitleFilter] = useState(TITLES[0]);
  const [tierFilter, setTierFilter] = useState(TIERS[0]);
  const [skillFilter, setSkillFilter] = useState(SKILLS[0]);
  const [timeframe, setTimeframe] = useState(TIMEFRAMES[1]);

  return (
    <div className="min-h-screen bg-[#0A0C10] text-zinc-100 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Trophy className="h-6 w-6 text-green-400" />
            Leaderboard
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            See how you stack up against the competition
          </p>
        </div>
      </div>

      {/* Your Position Card */}
      <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/5 border border-green-500/20 rounded-xl p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-green-500/20 rounded-full p-3">
              <Target className="h-6 w-6 text-green-400" />
            </div>
            <div>
              <p className="text-sm text-zinc-400">Your Position</p>
              <p className="text-2xl font-bold text-green-400">#1,247</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-zinc-400">Percentile</p>
            <p className="text-2xl font-bold text-zinc-100">
              Top <span className="text-green-400">34%</span>
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-zinc-400">Total Players</p>
            <p className="text-2xl font-bold text-zinc-300">3,672</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-zinc-900 rounded-lg p-1 w-fit">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-green-500/20 text-green-400'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {tab === 'By Title' && <Trophy className="inline h-4 w-4 mr-1.5" />}
            {tab === 'By Skill' && <Zap className="inline h-4 w-4 mr-1.5" />}
            {tab === 'Weekly Movers' && (
              <TrendingUp className="inline h-4 w-4 mr-1.5" />
            )}
            {tab}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-end gap-4 flex-wrap">
        <Filter className="h-5 w-5 text-zinc-500 mb-2" />
        <FilterDropdown label="Title" options={TITLES} value={titleFilter} onChange={setTitleFilter} />
        <FilterDropdown label="Tier" options={TIERS} value={tierFilter} onChange={setTierFilter} />
        <FilterDropdown label="Skill" options={SKILLS} value={skillFilter} onChange={setSkillFilter} />
        <FilterDropdown label="Timeframe" options={TIMEFRAMES} value={timeframe} onChange={setTimeframe} />
      </div>

      {/* Table */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-800 text-left">
              <th className="px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider w-16">
                Rank
              </th>
              <th className="px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider">
                Gamertag
              </th>
              <th className="px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider">
                Title
              </th>
              <th className="px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider text-right">
                Win Rate
              </th>
              <th className="px-5 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider text-right">
                Percentile
              </th>
            </tr>
          </thead>
          <tbody>
            {MOCK_PLAYERS.map((player) => (
              <tr
                key={player.rank}
                className="border-b border-zinc-800/50 hover:bg-zinc-800/40 transition-colors"
              >
                <td className="px-5 py-3">
                  <RankBadge rank={player.rank} />
                </td>
                <td className="px-5 py-3 font-medium text-zinc-100">
                  {player.gamertag}
                </td>
                <td className="px-5 py-3 text-sm text-zinc-400">{player.title}</td>
                <td className="px-5 py-3 text-sm text-right font-mono text-green-400">
                  {player.winRate}%
                </td>
                <td className="px-5 py-3 text-right">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">
                    Top {100 - player.percentile}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Opt-in Notice */}
      <div className="flex items-start gap-3 bg-zinc-900/40 border border-zinc-800 rounded-lg p-4">
        <Info className="h-5 w-5 text-zinc-500 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-zinc-500">
          Leaderboard participation is opt-in. Enable in{' '}
          <span className="text-green-400 font-medium">Settings &gt; Privacy</span> to
          appear in public rankings.
        </p>
      </div>
    </div>
  );
}

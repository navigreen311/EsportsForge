'use client';

import { useState } from 'react';
import {
  WinRateDataPoint,
  ModePerformance,
  WeaknessHeatmapEntry,
  AgentAccuracyEntry,
  SessionRecord,
  LoopAITrend,
} from '@/types/analytics';
import WinRateChart from '@/components/analytics/WinRateChart';
import WeaknessHeatmap from '@/components/analytics/WeaknessHeatmap';
import AgentAccuracy from '@/components/analytics/AgentAccuracy';
import BenchmarkRankSection from '@/components/analytics/BenchmarkRankSection';
import TransferGapChart from '@/components/analytics/TransferGapChart';
import ImpactRankROI from '@/components/analytics/ImpactRankROI';
import SituationalWinRates from '@/components/analytics/SituationalWinRates';
import PlayerTwinEvolution from '@/components/analytics/PlayerTwinEvolution';
import FatigueAnalytics from '@/components/analytics/FatigueAnalytics';
import SessionLoopAIDetails from '@/components/analytics/SessionLoopAIDetails';
import AnalyticsFilters from '@/components/analytics/AnalyticsFilters';
import ExportDropdown from '@/components/analytics/ExportDropdown';
import {
  BarChart3,
  Trophy,
  Swords,
  GraduationCap,
  ChevronDown,
  Brain,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

// --- Mock Data ---
const mockWinRateData: WinRateDataPoint[] = Array.from({ length: 30 }, (_, i) => ({
  date: `Mar ${i + 1}`,
  winRate: Math.round(45 + Math.random() * 30 + i * 0.5),
  sessions: Math.round(2 + Math.random() * 4),
}));

const mockModePerformance: ModePerformance[] = [
  { mode: 'ranked', totalGames: 48, wins: 31, losses: 17, winRate: 65, avgScore: 24 },
  { mode: 'tournament', totalGames: 12, wins: 9, losses: 3, winRate: 75, avgScore: 28 },
  { mode: 'training', totalGames: 35, wins: 22, losses: 13, winRate: 63, avgScore: 21 },
];

const mockWeaknessData: WeaknessHeatmapEntry[] = [
  { skill: 'Pre-Snap Reads', impactRank: 9, currentLevel: 62, targetLevel: 85, category: 'mental' },
  { skill: 'Blitz Recognition', impactRank: 8, currentLevel: 55, targetLevel: 80, category: 'defense' },
  { skill: 'Red Zone Offense', impactRank: 7, currentLevel: 45, targetLevel: 70, category: 'offense' },
  { skill: 'Clock Management', impactRank: 6, currentLevel: 58, targetLevel: 75, category: 'situational' },
  { skill: 'Route Combos', impactRank: 5, currentLevel: 70, targetLevel: 85, category: 'offense' },
  { skill: 'Run Defense', impactRank: 4, currentLevel: 72, targetLevel: 82, category: 'defense' },
  { skill: 'Audible Usage', impactRank: 4, currentLevel: 48, targetLevel: 70, category: 'mental' },
  { skill: 'Pocket Presence', impactRank: 3, currentLevel: 65, targetLevel: 78, category: 'offense' },
];

const mockAgentData: AgentAccuracyEntry[] = [
  { agentName: 'GameplanAgent', predictionsTotal: 120, predictionsCorrect: 102, accuracy: 85, trend: 'up', lastUpdated: '2h ago' },
  { agentName: 'OpponentScout', predictionsTotal: 85, predictionsCorrect: 68, accuracy: 80, trend: 'up', lastUpdated: '4h ago' },
  { agentName: 'DrillCoach', predictionsTotal: 60, predictionsCorrect: 45, accuracy: 75, trend: 'stable', lastUpdated: '1d ago' },
  { agentName: 'SituationAnalyzer', predictionsTotal: 95, predictionsCorrect: 66, accuracy: 69, trend: 'down', lastUpdated: '6h ago' },
];

const mockSessions: SessionRecord[] = [
  { id: 's1', date: '2026-03-22', mode: 'ranked', wins: 3, losses: 1, winRate: 75, opponentGamertag: 'xXDragonSlayerXx', score: '28-14', keyPlays: ['PA Crossers', 'Inside Zone'], duration: 45 },
  { id: 's2', date: '2026-03-21', mode: 'ranked', wins: 2, losses: 2, winRate: 50, opponentGamertag: 'AirRaidKing', score: '21-24', keyPlays: ['Four Verticals', 'HB Wham'], duration: 52 },
  { id: 's3', date: '2026-03-20', mode: 'tournament', wins: 4, losses: 0, winRate: 100, opponentGamertag: 'BlitzMaster99', score: '35-10', keyPlays: ['Mesh Concept', 'Wheel Route'], duration: 38 },
  { id: 's4', date: '2026-03-19', mode: 'training', wins: 2, losses: 3, winRate: 40, opponentGamertag: 'GridironGhost', score: '14-21', keyPlays: ['Stick Concept'], duration: 60 },
  { id: 's5', date: '2026-03-18', mode: 'ranked', wins: 3, losses: 2, winRate: 60, opponentGamertag: 'PocketGeneral', score: '24-17', keyPlays: ['Counter Run', 'QB Draw'], duration: 48 },
];

const mockLoopAI: LoopAITrend[] = Array.from({ length: 14 }, (_, i) => ({
  date: `Mar ${i + 9}`,
  learningScore: Math.round(40 + i * 3 + Math.random() * 8),
  adaptationRate: Math.round(30 + i * 2.5 + Math.random() * 10),
  predictionConfidence: Math.round(50 + i * 2 + Math.random() * 6),
}));

const modeIcons = {
  ranked: <Trophy className="w-4 h-4 text-yellow-400" />,
  tournament: <Swords className="w-4 h-4 text-red-400" />,
  training: <GraduationCap className="w-4 h-4 text-blue-400" />,
};

const modeColors = {
  ranked: 'bg-yellow-500/10 text-yellow-400 border-yellow-800/50',
  tournament: 'bg-red-500/10 text-red-400 border-red-800/50',
  training: 'bg-blue-500/10 text-blue-400 border-blue-800/50',
};

function LoopAITooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-lg px-4 py-3 shadow-xl">
      <p className="text-xs text-dark-400 mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} className="text-xs" style={{ color: p.stroke }}>
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  );
}

export default function AnalyticsPage() {
  const [expandedSession, setExpandedSession] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      {/* Header + Export */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-50 flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-forge-400" />
            Analytics
          </h1>
          <p className="text-dark-400 mt-1">Performance intelligence dashboard</p>
        </div>
        {/* 9. Export Dropdown */}
        <ExportDropdown />
      </div>

      {/* 8. Analytics Filters Bar */}
      <AnalyticsFilters />

      {/* Top Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Overall Win Rate', value: '65%', change: '+3%', positive: true },
          { label: 'Total Sessions', value: '95', change: '+12', positive: true },
          { label: 'Current Streak', value: 'W3', change: '', positive: true },
          { label: 'Avg Score Diff', value: '+7.2', change: '+1.4', positive: true },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-xl border border-dark-700 bg-dark-900/50 p-4"
          >
            <p className="text-xs text-dark-500 uppercase tracking-wider">{stat.label}</p>
            <div className="flex items-end gap-2 mt-1">
              <span className="text-2xl font-bold font-mono text-dark-50">{stat.value}</span>
              {stat.change && (
                <span
                  className={`text-xs font-medium ${
                    stat.positive ? 'text-forge-400' : 'text-red-400'
                  }`}
                >
                  {stat.change}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* 1. BenchmarkAI Competitive Rank */}
      <BenchmarkRankSection />

      {/* Win Rate Chart */}
      <WinRateChart data={mockWinRateData} />

      {/* Performance by Mode */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h2 className="text-lg font-bold text-dark-100 mb-4">Performance by Mode</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {mockModePerformance.map((mode) => (
            <div
              key={mode.mode}
              className={`rounded-lg border p-4 ${modeColors[mode.mode]}`}
            >
              <div className="flex items-center gap-2 mb-3">
                {modeIcons[mode.mode]}
                <span className="text-sm font-bold capitalize">{mode.mode}</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-dark-400">Win Rate</span>
                  <span className="font-mono font-bold">{mode.winRate}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-dark-400">Record</span>
                  <span className="font-mono">{mode.wins}-{mode.losses}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-dark-400">Avg Score</span>
                  <span className="font-mono">{mode.avgScore}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. Situational Win Rates */}
      <SituationalWinRates />

      {/* 2. TransferAI Lab-to-Live Gap Chart */}
      <TransferGapChart />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weakness Heatmap */}
        <WeaknessHeatmap data={mockWeaknessData} />

        {/* Agent Accuracy */}
        <AgentAccuracy agents={mockAgentData} />
      </div>

      {/* 3. ImpactRank ROI */}
      <ImpactRankROI />

      {/* LoopAI Learning Trend */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <div className="flex items-center gap-3 mb-5">
          <Brain className="w-5 h-5 text-purple-400" />
          <div>
            <h2 className="text-lg font-bold text-dark-100">LoopAI Learning Trend</h2>
            <p className="text-sm text-dark-400">System adaptation over time</p>
          </div>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mockLoopAI} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} domain={[0, 100]} />
              <Tooltip content={<LoopAITooltip />} />
              <Line type="monotone" dataKey="learningScore" name="Learning" stroke="#a855f7" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="adaptationRate" name="Adaptation" stroke="#22c55e" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="predictionConfidence" name="Confidence" stroke="#3b82f6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-center gap-6 mt-4 text-xs">
          <span className="flex items-center gap-1.5"><span className="w-3 h-1 rounded bg-purple-500" /> Learning</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-1 rounded bg-forge-500" /> Adaptation</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-1 rounded bg-blue-500" /> Confidence</span>
        </div>
      </div>

      {/* 5. PlayerTwin Evolution */}
      <PlayerTwinEvolution />

      {/* 6. Fatigue Analytics */}
      <FatigueAnalytics />

      {/* Session History with 7. LoopAI columns */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h2 className="text-lg font-bold text-dark-100 mb-4">Session History</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700">
                <th className="text-left py-3 px-3 text-dark-500 font-medium text-xs uppercase tracking-wider">Date</th>
                <th className="text-left py-3 px-3 text-dark-500 font-medium text-xs uppercase tracking-wider">Mode</th>
                <th className="text-left py-3 px-3 text-dark-500 font-medium text-xs uppercase tracking-wider">Opponent</th>
                <th className="text-left py-3 px-3 text-dark-500 font-medium text-xs uppercase tracking-wider">Score</th>
                <th className="text-left py-3 px-3 text-dark-500 font-medium text-xs uppercase tracking-wider">Win Rate</th>
                <th className="text-left py-3 px-3 text-dark-500 font-medium text-xs uppercase tracking-wider">Duration</th>
                <th className="py-3 px-3"></th>
              </tr>
            </thead>
            <tbody>
              {mockSessions.map((session) => (
                <>
                  <tr
                    key={session.id}
                    className="border-b border-dark-800 hover:bg-dark-800/30 cursor-pointer transition-colors"
                    onClick={() =>
                      setExpandedSession(
                        expandedSession === session.id ? null : session.id
                      )
                    }
                  >
                    <td className="py-3 px-3 text-dark-300">{session.date}</td>
                    <td className="py-3 px-3">
                      <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium border ${modeColors[session.mode]}`}>
                        {modeIcons[session.mode]}
                        {session.mode}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-dark-200 font-medium">{session.opponentGamertag}</td>
                    <td className="py-3 px-3 font-mono text-dark-200">{session.score}</td>
                    <td className="py-3 px-3">
                      <span className={`font-mono font-bold ${session.winRate >= 50 ? 'text-forge-400' : 'text-red-400'}`}>
                        {session.winRate}%
                      </span>
                    </td>
                    <td className="py-3 px-3 text-dark-400">{session.duration}m</td>
                    <td className="py-3 px-3">
                      <ChevronDown
                        className={`w-4 h-4 text-dark-500 transition-transform ${
                          expandedSession === session.id ? 'rotate-180' : ''
                        }`}
                      />
                    </td>
                  </tr>
                  {expandedSession === session.id && (
                    <tr key={`${session.id}-detail`} className="border-b border-dark-800">
                      <td colSpan={7} className="py-4 px-6 bg-dark-800/20">
                        <div className="space-y-4">
                          {/* Existing details */}
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <p className="text-xs text-dark-500 uppercase tracking-wider mb-1">Record</p>
                              <p className="text-sm text-dark-200">{session.wins}W - {session.losses}L</p>
                            </div>
                            <div>
                              <p className="text-xs text-dark-500 uppercase tracking-wider mb-1">Key Plays</p>
                              <div className="flex flex-wrap gap-1">
                                {session.keyPlays.map((play) => (
                                  <span key={play} className="px-2 py-0.5 text-xs bg-forge-500/10 text-forge-400 rounded border border-forge-800/30">
                                    {play}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                          {/* 7. LoopAI Session Details */}
                          <SessionLoopAIDetails sessionId={session.id} />
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

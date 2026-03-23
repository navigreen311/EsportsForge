'use client';

import { useState } from 'react';
import type {
  DashboardData,
  PriorityItem,
  RecommendationItem,
  WeeklyNarrativeData,
  QuickAction,
  SessionStatus,
  TournamentInfo,
  DashboardStats,
  FatigueIndicator,
  ExecutionGap,
  LoopAIDebrief,
  BenchmarkMetric,
  ProgressionPackage,
} from '@/types/dashboard';

const mockPriority: PriorityItem = {
  id: 'pri-1',
  weakness: 'Coverage Read Speed',
  category: 'mental',
  winRateDamage: 8.3,
  expectedLift: 5.7,
  timeToMaster: '2-3 weeks',
  confidence: 87,
  impactRank: 9.4,
};

const mockPriorities: PriorityItem[] = [
  mockPriority,
  {
    id: 'pri-2',
    weakness: 'Red Zone Efficiency',
    category: 'situational',
    winRateDamage: 5.1,
    expectedLift: 3.9,
    timeToMaster: '1-2 weeks',
    confidence: 82,
    impactRank: 7.8,
  },
  {
    id: 'pri-3',
    weakness: 'Blitz Recognition',
    category: 'defense',
    winRateDamage: 4.2,
    expectedLift: 3.1,
    timeToMaster: '3-4 weeks',
    confidence: 76,
    impactRank: 6.5,
  },
];

const mockStats: DashboardStats = {
  winRate: 67,
  totalGames: 142,
  currentStreak: 8,
  readiness: 84,
};

const mockRecommendations: RecommendationItem[] = [
  {
    id: 'rec-1',
    agentSource: 'GameplanAgent',
    text: 'Switch to Cover 3 Sky against spread formations — your Cover 2 has been exploited in 4 of last 6 games.',
    confidence: 91,
    outcome: 'followed',
    timestamp: '2h ago',
    proof: {
      reason: 'Cover 2 exploited 4/6 games vs spread — opponents averaging 8.2 YPA',
      dataSource: 'Last 6 games vs spread formation opponents',
      riskIfIgnored: 'Exposed on wheel route if opponent motions the back out of backfield',
    },
  },
  {
    id: 'rec-2',
    agentSource: 'DrillCoach',
    text: 'Add pre-snap read drills to your warm-up. Your read speed is 23% below your target.',
    confidence: 85,
    outcome: 'followed',
    timestamp: '5h ago',
    proof: {
      reason: 'Read speed avg 1.8s vs 1.4s target — costing 2.1 win-rate points',
      dataSource: 'PlayerTwin read-speed telemetry, 30-day trend',
      riskIfIgnored: 'Read speed regression likely if not drilled within 48h',
    },
  },
  {
    id: 'rec-3',
    agentSource: 'OpponentScout',
    text: 'xXDragonSlayerXx favors HB Dive on 3rd & short — stack the box.',
    confidence: 78,
    outcome: 'pending',
    timestamp: '1d ago',
    proof: {
      reason: 'HB Dive called 72% of 3rd-and-short by this opponent (18/25 plays)',
      dataSource: 'OpponentScout encounter history, 8 games tracked',
      riskIfIgnored: 'Opponent converts 3rd down at 68% if box isn\'t stacked',
    },
  },
  {
    id: 'rec-4',
    agentSource: 'SituationAnalyzer',
    text: 'Your red zone efficiency drops 18% in the 4th quarter — practice clutch scoring scenarios.',
    confidence: 82,
    outcome: 'ignored',
    timestamp: '1d ago',
    proof: {
      reason: '4th quarter RZ efficiency 41% vs 59% in quarters 1-3',
      dataSource: 'Session analytics, last 20 games with RZ attempts',
      riskIfIgnored: 'Estimated 1.4 points per game left on the table in close matches',
    },
  },
  {
    id: 'rec-5',
    agentSource: 'GameplanAgent',
    text: 'PA Crossers has a 74% success rate vs man coverage — make it your go-to on 2nd & medium.',
    confidence: 88,
    outcome: 'followed',
    timestamp: '2d ago',
    proof: {
      reason: 'PA Crossers success rate 74% vs man (23/31 plays) — 12.4 avg yards',
      dataSource: 'Play-level analytics, current season',
      riskIfIgnored: '2nd & medium conversion rate stays at 48% instead of projected 61%',
    },
  },
];

const mockNarrative: WeeklyNarrativeData = {
  weekLabel: 'Week of Mar 16 – 22',
  narrative:
    'This week you hit a new stride. Your win rate climbed to 67% — up 5 points from last week — driven by sharper pre-snap reads and better clutch execution. The 8-game streak is your longest this season. Your biggest remaining gap is coverage read speed, but the DrillCoach sees strong momentum if you stay consistent with your daily reps.',
  milestones: [
    { label: '8-Game Win Streak', achieved: true },
    { label: '67% Win Rate', achieved: true },
    { label: 'Pre-Snap Reads +12%', achieved: true },
  ],
};

const mockQuickActions: QuickAction[] = [
  {
    id: 'qa-1',
    label: 'Generate Gameplan',
    description: 'AI-powered strategy for your next match',
    href: '/gameplan',
    icon: 'Gamepad2',
  },
  {
    id: 'qa-2',
    label: 'Start Drill',
    description: 'Practice your weakest skills',
    href: '/drills',
    icon: 'Target',
  },
  {
    id: 'qa-3',
    label: 'Scout Opponent',
    description: 'Analyze your next rival',
    href: '/opponents',
    icon: 'Users',
  },
  {
    id: 'qa-4',
    label: 'View Analytics',
    description: 'Deep dive into your performance',
    href: '/analytics',
    icon: 'BarChart3',
  },
];

const mockSession: SessionStatus | null = null;

const mockTournament: TournamentInfo | null = {
  id: 'tourney-1',
  name: 'Weekend Warrior Cup #14',
  date: '2026-03-28',
  format: 'Single Elimination Bo3',
  registeredPlayers: 64,
  status: 'upcoming',
};

const mockFatigue: FatigueIndicator = {
  peakWindowMinutes: 75,
  currentSessionMinutes: null,
  status: 'fresh',
};

const mockExecutionGap: ExecutionGap = {
  skill: 'Coverage Reads',
  drillRate: 91,
  rankedRate: 54,
  drillId: 'drill-coverage-reads',
};

const mockDebrief: LoopAIDebrief | null = {
  gameTimestamp: '2h ago',
  recommendation: 'Switch to Cover 3 Sky against spread formations',
  wasFollowed: true,
  outcome: 'won',
  loopUpdate: 'Boosted Cover 3 Sky confidence to 91% for spread matchups',
};

const mockBenchmarks: BenchmarkMetric[] = [
  { label: 'Read Speed', percentile: 72 },
  { label: 'Clutch Conversion', percentile: 34 },
  { label: 'User Defense', percentile: 58 },
  { label: 'Execution Under Pressure', percentile: 81 },
];

const mockProgressionCurrent: ProgressionPackage = {
  name: 'Base Pass Concepts',
  percentComplete: 67,
};

const mockProgressionNext: ProgressionPackage = {
  name: 'Pressure Package',
  percentComplete: 0,
};

export function useDashboard() {
  const [data] = useState<DashboardData>({
    username: 'Commander',
    stats: mockStats,
    priority: mockPriority,
    priorities: mockPriorities,
    recentRecommendations: mockRecommendations,
    weeklyNarrative: mockNarrative,
    quickActions: mockQuickActions,
    activeSession: mockSession,
    upcomingTournament: mockTournament,
    fatigue: mockFatigue,
    executionGap: mockExecutionGap,
    lastDebrief: mockDebrief,
    benchmarks: mockBenchmarks,
    progression: { current: mockProgressionCurrent, next: mockProgressionNext },
  });

  const isLoading = false;

  return { data, isLoading };
}

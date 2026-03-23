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
  },
  {
    id: 'rec-2',
    agentSource: 'DrillCoach',
    text: 'Add pre-snap read drills to your warm-up. Your read speed is 23% below your target.',
    confidence: 85,
    outcome: 'followed',
    timestamp: '5h ago',
  },
  {
    id: 'rec-3',
    agentSource: 'OpponentScout',
    text: 'xXDragonSlayerXx favors HB Dive on 3rd & short — stack the box.',
    confidence: 78,
    outcome: 'pending',
    timestamp: '1d ago',
  },
  {
    id: 'rec-4',
    agentSource: 'SituationAnalyzer',
    text: 'Your red zone efficiency drops 18% in the 4th quarter — practice clutch scoring scenarios.',
    confidence: 82,
    outcome: 'ignored',
    timestamp: '1d ago',
  },
  {
    id: 'rec-5',
    agentSource: 'GameplanAgent',
    text: 'PA Crossers has a 74% success rate vs man coverage — make it your go-to on 2nd & medium.',
    confidence: 88,
    outcome: 'followed',
    timestamp: '2d ago',
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

export function useDashboard() {
  const [data] = useState<DashboardData>({
    username: 'Commander',
    stats: mockStats,
    priority: mockPriority,
    recentRecommendations: mockRecommendations,
    weeklyNarrative: mockNarrative,
    quickActions: mockQuickActions,
    activeSession: mockSession,
    upcomingTournament: mockTournament,
  });

  const isLoading = false;

  return { data, isLoading };
}

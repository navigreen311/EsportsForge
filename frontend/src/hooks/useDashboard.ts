'use client';

import { useMemo } from 'react';
import { useUIStore } from '@/lib/store';
import { getDashboardDataForTitle } from '@/lib/titleMockData';
import type {
  DashboardData,
  QuickAction,
  SessionStatus,
  TournamentInfo,
  FatigueIndicator,
} from '@/types/dashboard';

const quickActions: QuickAction[] = [
  { id: 'qa-1', label: 'Generate Gameplan', description: 'AI-powered strategy for your next match', href: '/gameplan', icon: 'Gamepad2' },
  { id: 'qa-2', label: 'Start Drill', description: 'Practice your weakest skills', href: '/drills', icon: 'Target' },
  { id: 'qa-3', label: 'Scout Opponent', description: 'Analyze your next rival', href: '/opponents', icon: 'Users' },
  { id: 'qa-4', label: 'View Analytics', description: 'Deep dive into your performance', href: '/analytics', icon: 'BarChart3' },
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

export function useDashboard() {
  const selectedTitle = useUIStore((s) => s.selectedTitle);

  const data = useMemo<DashboardData>(() => {
    const titleData = getDashboardDataForTitle(selectedTitle);

    return {
      username: 'Commander',
      stats: titleData.stats,
      priority: titleData.priorities[0] ?? {
        id: 'empty',
        weakness: 'No priorities yet',
        category: 'mental' as const,
        winRateDamage: 0,
        expectedLift: 0,
        timeToMaster: 'N/A',
        confidence: 0,
        impactRank: 0,
      },
      priorities: titleData.priorities,
      recentRecommendations: titleData.recommendations,
      weeklyNarrative: titleData.narrative,
      quickActions,
      activeSession: mockSession,
      upcomingTournament: titleData.hasData ? mockTournament : null,
      fatigue: mockFatigue,
      executionGap: titleData.executionGap,
      lastDebrief: titleData.debrief,
      benchmarks: titleData.benchmarks,
      progression: titleData.progression,
    };
  }, [selectedTitle]);

  const isLoading = false;
  const hasData = getDashboardDataForTitle(selectedTitle).hasData;
  const statLabels = getDashboardDataForTitle(selectedTitle).statLabels;

  return { data, isLoading, hasData, statLabels };
}

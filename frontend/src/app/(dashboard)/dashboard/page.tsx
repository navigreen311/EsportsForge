/**
 * Dashboard — Main landing page after login.
 * Shows priority weakness, stats, recommendations, narrative, quick actions.
 */

'use client';

import {
  LayoutDashboard,
  Flame,
  Percent,
  Gamepad2,
  Zap,
  Activity,
  Trophy,
  CalendarDays,
} from 'lucide-react';
import { useDashboard } from '@/hooks/useDashboard';
import { StatCard } from '@/components/shared/StatCard';
import { Card } from '@/components/shared/Card';
import { Badge } from '@/components/shared/Badge';
import PriorityCard from '@/components/dashboard/PriorityCard';
import RecentRecommendations from '@/components/dashboard/RecentRecommendations';
import WeeklyNarrative from '@/components/dashboard/WeeklyNarrative';
import QuickActions from '@/components/dashboard/QuickActions';
import SessionIndicator from '@/components/dashboard/SessionIndicator';

export default function DashboardPage() {
  const { data } = useDashboard();

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold text-dark-50">
            <LayoutDashboard className="h-8 w-8 text-forge-400" />
            Welcome back, {data.username}
          </h1>
          <p className="mt-1 text-dark-400">
            Here&apos;s your competitive intelligence briefing.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Streak badge */}
          <Badge variant="success" dot>
            <Flame className="h-3.5 w-3.5" />
            {data.stats.currentStreak}-Game Streak
          </Badge>

          {/* Session indicator */}
          <SessionIndicator session={data.activeSession} />
        </div>
      </div>

      {/* Priority Card */}
      <PriorityCard priority={data.priority} />

      {/* Stat Cards Row */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Win Rate"
          value={`${data.stats.winRate}%`}
          trend={{ direction: 'up', value: '+5% this week' }}
          sparklineData={[52, 55, 58, 61, 59, 63, 65, 67]}
          icon={<Percent className="h-4 w-4" />}
        />
        <StatCard
          label="Games Played"
          value={data.stats.totalGames}
          trend={{ direction: 'up', value: '+12 this week' }}
          sparklineData={[98, 105, 112, 118, 126, 131, 138, 142]}
          icon={<Gamepad2 className="h-4 w-4" />}
        />
        <StatCard
          label="Win Streak"
          value={`W${data.stats.currentStreak}`}
          trend={{ direction: 'up', value: 'Season best' }}
          sparklineData={[1, 0, 3, 2, 0, 4, 6, 8]}
          icon={<Zap className="h-4 w-4" />}
        />
        <StatCard
          label="Readiness"
          value={`${data.stats.readiness}%`}
          trend={{ direction: 'up', value: '+3 pts' }}
          sparklineData={[72, 74, 78, 76, 80, 81, 83, 84]}
          icon={<Activity className="h-4 w-4" />}
        />
      </div>

      {/* Two-column: Recommendations + Narrative */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <RecentRecommendations
          recommendations={data.recentRecommendations}
        />
        <div className="space-y-6">
          <WeeklyNarrative narrative={data.weeklyNarrative} />

          {/* Upcoming Tournament */}
          {data.upcomingTournament && (
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10">
                  <Trophy className="h-5 w-5 text-amber-400" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-bold text-dark-100">
                    {data.upcomingTournament.name}
                  </p>
                  <div className="flex items-center gap-2 text-[11px] text-dark-400">
                    <CalendarDays className="h-3 w-3" />
                    <span>{data.upcomingTournament.date}</span>
                    <span className="text-dark-600">|</span>
                    <span>{data.upcomingTournament.format}</span>
                    <span className="text-dark-600">|</span>
                    <span>
                      {data.upcomingTournament.registeredPlayers} players
                    </span>
                  </div>
                </div>
                <Badge variant="warning" size="sm">
                  Upcoming
                </Badge>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <QuickActions actions={data.quickActions} />
    </div>
  );
}

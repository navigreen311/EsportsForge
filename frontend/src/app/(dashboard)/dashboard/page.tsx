/**
 * Dashboard — Main landing page after login.
 * - Idle mode: TiltGuard check-in, priority weakness stack, stats, fatigue,
 *   benchmarks, progression, recommendations, narrative, quick actions.
 * - Competition mode: takes over the top of the page when a session is live —
 *   competition card, post-game flow modals, session timeline at the bottom.
 */

'use client';

import { useEffect, useState } from 'react';
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
import { useUIStore } from '@/lib/store';
import { useSessionStore, useSessionUIStore } from '@/lib/sessionStore';
import { getTitleById } from '@/lib/titles';
import { TitleEmptyState } from '@/components/shared/TitleEmptyState';
import { StatCard } from '@/components/shared/StatCard';
import { Card } from '@/components/shared/Card';
import { Badge } from '@/components/shared/Badge';
import PriorityCard from '@/components/dashboard/PriorityCard';
import PriorityStack from '@/components/dashboard/PriorityStack';
import RecentRecommendations from '@/components/dashboard/RecentRecommendations';
import WeeklyNarrative from '@/components/dashboard/WeeklyNarrative';
import QuickActions from '@/components/dashboard/QuickActions';
import SessionIndicator from '@/components/dashboard/SessionIndicator';
import { SessionStartCard } from '@/components/dashboard/SessionStartCard';
import { LogMatchModal, type MatchLogPayload } from '@/components/dashboard/LogMatchModal';
import { SessionReviewModal, type SessionReviewPayload } from '@/components/dashboard/SessionReviewModal';
import TiltGuardCheckin, {
  MoodBadge,
  loadStoredMood,
} from '@/components/dashboard/TiltGuardCheckin';
import FatigueIndicatorCard from '@/components/dashboard/FatigueIndicator';
import ExecutionGapCard from '@/components/dashboard/ExecutionGapCard';
import LoopAIDebriefCard from '@/components/dashboard/LoopAIDebriefCard';
import BenchmarkPanel from '@/components/dashboard/BenchmarkPanel';
import ProgressionStrip from '@/components/dashboard/ProgressionStrip';
import { DailyForgeCard } from '@/components/dailyforge/DailyForgeCard';
import TransferAIWidget from '@/components/dashboard/TransferAIWidget';
import LoopAIDebrief from '@/components/dashboard/LoopAIDebrief';
import ProofAIPanel from '@/components/dashboard/ProofAIPanel';
import { CompetitionModeCard } from '@/components/session/CompetitionModeCard';
import { SessionTimeline } from '@/components/session/SessionTimeline';
import {
  PostGameResultModal,
  LoopAIUpdateModal,
} from '@/components/session/PostGameFlow';
import type { TiltGuardMood } from '@/types/dashboard';
import type { SessionGameResult } from '@/lib/sessionStore';

type PostGamePhase = 'idle' | 'result' | 'loopai';

export default function DashboardPage() {
  const { data, hasData, statLabels } = useDashboard();
  const [mood, setMood] = useState<TiltGuardMood | null>(null);
  const [moodModalOpen, setMoodModalOpen] = useState<boolean | undefined>(undefined);
  const [logMatchOpen, setLogMatchOpen] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [postGamePhase, setPostGamePhase] = useState<PostGamePhase>('idle');
  const [pendingResult, setPendingResult] = useState<SessionGameResult | null>(null);

  const selectedTitle = useUIStore((s) => s.selectedTitle);
  const titleInfo = getTitleById(selectedTitle);
  const session = useSessionStore((s) => s.session);
  const recordResult = useSessionStore((s) => s.recordResult);
  const startNextGame = useSessionStore((s) => s.startNextGame);
  const endSession = useSessionStore((s) => s.endSession);
  const requestEnd = useSessionUIStore((s) => s.requestEnd);

  const isSessionActive = !!session;
  const opponent = session?.opponent ?? 'Next Opponent';
  const killShotName = data.priority?.weakness ?? 'Top Play';

  useEffect(() => {
    const stored = loadStoredMood();
    if (stored) setMood(stored);
  }, []);

  const handleLogMatchSubmit = (payload: MatchLogPayload) => {
    console.info('[match-log]', payload);
    setLogMatchOpen(false);
  };

  const handleReviewSubmit = (payload: SessionReviewPayload) => {
    console.info('[session-review]', payload);
    endSession();
    setReviewOpen(false);
  };

  const handleReviewSkip = () => {
    endSession();
    setReviewOpen(false);
  };

  const handlePostGameResult = (result: SessionGameResult) => {
    recordResult(result);
    setPendingResult(result);
    setPostGamePhase('loopai');
  };

  const handlePlayAnother = () => {
    startNextGame();
    setPendingResult(null);
    setPostGamePhase('idle');
  };

  const handleEndFromLoopAI = () => {
    setPostGamePhase('idle');
    setPendingResult(null);
    requestEnd();
  };

  return (
    <div className="space-y-6">
      {/* TiltGuard Pre-Session Check-In Modal */}
      <TiltGuardCheckin
        onMoodSelect={setMood}
        open={moodModalOpen}
        onOpenChange={(o) => setMoodModalOpen(o ? true : undefined)}
      />

      {/* Welcome Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold text-dark-50">
            <LayoutDashboard className="h-8 w-8 text-forge-400" />
            Welcome back, {data.username}
          </h1>
          <p className="mt-1 text-dark-400">
            {isSessionActive
              ? 'Competition mode is live. Stay focused.'
              : "Here's your competitive intelligence briefing."}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <MoodBadge mood={mood} onUpdate={() => setMoodModalOpen(true)} />
          <Badge variant="success" dot>
            <Flame className="h-3.5 w-3.5" />
            {data.stats.currentStreak}-Game Streak
          </Badge>
          <SessionIndicator
            onLogMatch={() => setLogMatchOpen(true)}
            onEndSession={() => requestEnd()}
          />
        </div>
      </div>

      {/* Empty state for titles with no data */}
      {!hasData && titleInfo && (
        <TitleEmptyState titleName={titleInfo.name} titleIcon={titleInfo.icon} />
      )}

      {/* Competition mode — replaces idle hero when session is live */}
      {isSessionActive ? (
        <CompetitionModeCard
          onLogResult={() => setPostGamePhase('result')}
          onMentalReset={() => setMoodModalOpen(true)}
        />
      ) : (
        <>
          <DailyForgeCard />
          <SessionStartCard onLogMatch={() => setLogMatchOpen(true)} />
        </>
      )}

      {/* Priority Card — #1 */}
      {hasData && <PriorityCard priority={data.priority} />}

      {/* ProgressionOS Install Roadmap Strip */}
      {hasData && <ProgressionStrip
        current={data.progression.current}
        next={data.progression.next}
      />}

      {/* ImpactRank Priority Stack — #2 and #3 */}
      {hasData && <PriorityStack priorities={data.priorities} />}

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
          label={statLabels.games}
          value={data.stats.totalGames}
          trend={{ direction: 'up', value: '+12 this week' }}
          sparklineData={[98, 105, 112, 118, 126, 131, 138, 142]}
          icon={<Gamepad2 className="h-4 w-4" />}
        />
        <StatCard
          label={statLabels.streak}
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

      {/* Predictive Fatigue Indicator */}
      <FatigueIndicatorCard data={data.fatigue} />

      {/* TransferAI Execution Gap */}
      <ExecutionGapCard gap={data.executionGap} />

      {/* TransferAI Lab vs Live Widget */}
      <TransferAIWidget />

      {/* BenchmarkAI Percentile Panel */}
      <BenchmarkPanel benchmarks={data.benchmarks} />

      {/* Two-column: Recommendations + Narrative */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <LoopAIDebriefCard debrief={data.lastDebrief} />
          <LoopAIDebrief />
          <RecentRecommendations recommendations={data.recentRecommendations} />
        </div>

        <div className="space-y-6">
          <ProofAIPanel />
          <WeeklyNarrative narrative={data.weeklyNarrative} />

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
                <Badge variant="warning" size="sm">Upcoming</Badge>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <QuickActions actions={data.quickActions} />

      {/* Session timeline (only during competition mode) */}
      {isSessionActive && <SessionTimeline />}

      {/* Idle/legacy modals */}
      <LogMatchModal
        open={logMatchOpen}
        onClose={() => setLogMatchOpen(false)}
        onSubmit={handleLogMatchSubmit}
      />
      <SessionReviewModal
        open={reviewOpen}
        onClose={() => setReviewOpen(false)}
        onSubmit={handleReviewSubmit}
        onSkip={handleReviewSkip}
      />

      {/* Competition-mode post-game flow */}
      <PostGameResultModal
        open={postGamePhase === 'result'}
        opponent={opponent}
        killShotName={killShotName}
        onClose={() => setPostGamePhase('idle')}
        onSubmit={handlePostGameResult}
      />
      <LoopAIUpdateModal
        open={postGamePhase === 'loopai'}
        killShotName={killShotName}
        result={pendingResult}
        onClose={() => setPostGamePhase('idle')}
        onPlayAnother={handlePlayAnother}
        onEndSession={handleEndFromLoopAI}
      />
    </div>
  );
}

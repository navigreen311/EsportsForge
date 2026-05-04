'use client';

import { Suspense, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Eye, Play, Swords, Target } from 'lucide-react';
import { useDrills } from '@/hooks/useDrills';
import { useUIStore } from '@/lib/store';
import PreDrillBriefModal from '@/components/drills/PreDrillBriefModal';
import type { ActiveDrillResult } from '@/components/drills/ActiveDrillMode';
import ActiveDrillPiPHost from '@/components/drills/ActiveDrillPiPHost';
import DrillDebrief from '@/components/drills/DrillDebrief';
import type { RepDot } from '@/components/drills/RepTracker';
import type { DrillDebriefDTO } from '@/lib/api/drillSessions';
import { VisionAudioForgeService } from '@/lib/services/visionaudioforge';
import { speakBrief } from '@/lib/drills/voice';

const visionMonitor = {
  start: ({
    drill,
    titleId,
    onRep,
  }: {
    drill: import('@/types/analytics').DrillRecord;
    titleId: string;
    onRep: (success: boolean, confidence?: number, reason?: string) => void;
  }) => VisionAudioForgeService.startDrillMonitoring({ drill, titleId, onRep }),
  stop: () => VisionAudioForgeService.stopDrillMonitoring(),
};
import DrillRunner from '@/components/drills/DrillRunner';
import DrillQueue from '@/components/drills/DrillQueue';
import SkillProgress from '@/components/drills/SkillProgress';
import DrillSummary from '@/components/drills/DrillSummary';
import TransferReadinessPanel from '@/components/drills/TransferReadinessPanel';
import InputLabPanel from '@/components/drills/InputLabPanel';
import SessionFatigueBar from '@/components/drills/SessionFatigueBar';
import DrillDebriefModal from '@/components/drills/DrillDebriefModal';
import PostDrillDebrief from '@/components/drills/PostDrillDebrief';
import TransferAIReadiness from '@/components/drills/TransferAIReadiness';
import DrillStreakWidget from '@/components/drills/DrillStreakWidget';
import { DrillStreak } from '@/components/drills/DrillStreakTracker';
import { MonthlyConsistency } from '@/components/drills/DrillStreakTracker';

function PriorityBanner() {
  const params = useSearchParams();
  const priority = params.get('priority');
  if (!priority) return null;
  return (
    <div className="flex items-center gap-3 rounded-lg border border-forge-500/30 bg-forge-500/10 px-4 py-3">
      <Target className="h-5 w-5 shrink-0 text-forge-400" />
      <p className="text-sm text-dark-100">
        Fixing: <span className="font-bold text-forge-400">{priority}</span>
        <span className="text-dark-400"> — your #1 ImpactRank priority</span>
      </p>
    </div>
  );
}

function DrillsPageInner() {
  const {
    currentDrill,
    queue,
    session,
    skillProgress,
    successCount,
    failCount,
    totalReps,
    totalTargetReps,
    overallSuccessRate,
    startDrill,
    completeRep,
    skipDrill,
    nextDrill,
    endSession,
    resetSession,
    lastCompletedDrill,
    clearLastCompleted,
  } = useDrills();

  const titleId = useUIStore((s) => s.selectedTitle);

  const [sessionStart] = useState<Date | null>(() => new Date());
  const [showDebrief, setShowDebrief] = useState(false);
  const [showPostDebrief, setShowPostDebrief] = useState(false);

  // Active-drill flow (PreBrief → ActiveDrillMode → Debrief)
  const [briefOpen, setBriefOpen] = useState(false);
  const [activeDrill, setActiveDrill] = useState<typeof currentDrill | null>(null);
  const [debriefData, setDebriefData] = useState<{
    drill: NonNullable<typeof currentDrill>;
    debrief: DrillDebriefDTO;
    reps: RepDot[];
  } | null>(null);

  const handleBeginActiveDrill = () => {
    if (currentDrill) setBriefOpen(true);
  };
  const handleStartActiveDrill = () => {
    if (currentDrill) {
      speakBrief(
        currentDrill.name,
        currentDrill.objective ?? currentDrill.instructions,
      );
    }
    setBriefOpen(false);
    setActiveDrill(currentDrill);
  };
  const handleActiveComplete = (result: ActiveDrillResult) => {
    setActiveDrill(null);
    setDebriefData({ drill: result.drill, debrief: result.debrief, reps: result.reps });
  };
  const handleActiveAbort = () => {
    setActiveDrill(null);
  };
  const handleDebriefNext = () => {
    setDebriefData(null);
    nextDrill();
  };
  const handleDebriefEnd = () => {
    setDebriefData(null);
  };

  const completedDrillCount = session.completedDrills.length;

  useEffect(() => {
    if (lastCompletedDrill) {
      setShowDebrief(true);
    }
  }, [lastCompletedDrill]);

  // Post-drill summary view
  if (session.sessionComplete) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-dark-50 flex items-center gap-3">
            <Swords className="w-8 h-8 text-forge-400" />
            Drill Lab
          </h1>
          <p className="text-dark-400 mt-1">Session complete</p>
        </div>
        <DrillSummary
          completedDrills={session.completedDrills}
          totalReps={totalReps}
          overallSuccessRate={overallSuccessRate}
          skillProgress={skillProgress}
          onReset={resetSession}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-50 flex items-center gap-3">
            <Swords className="w-8 h-8 text-forge-400" />
            Drill Lab
          </h1>
          <p className="text-dark-400 mt-1">
            ImpactRank-ordered training drills with dynamic calibration
          </p>
        </div>

        {/* Session Progress + Streak */}
        <div className="text-right hidden md:block space-y-1">
          <p className="text-sm text-dark-400">Session Progress</p>
          <p className="text-lg font-bold font-mono text-dark-100">
            {totalReps}/{totalTargetReps}{' '}
            <span className="text-sm text-dark-500 font-normal">reps</span>
          </p>
          {/* 9. Drill Streak */}
          <DrillStreak />
        </div>
      </div>

      <PriorityBanner />

      {/* Active drill replaces the queue/runner while a session is in flight */}
      {activeDrill ? (
        <ActiveDrillPiPHost
          drill={activeDrill}
          titleId={titleId}
          monitor={visionMonitor}
          onComplete={handleActiveComplete}
          onAbort={handleActiveAbort}
        />
      ) : (
        currentDrill && (
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-forge-500/30 bg-dark-900/60 p-4">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-forge-400">
                Ready to run
              </p>
              <p className="mt-0.5 text-sm font-bold text-dark-50">{currentDrill.name}</p>
              <p className="text-xs text-dark-400">
                {currentDrill.reps} reps · IR {currentDrill.impactRank}
              </p>
            </div>
            <button
              type="button"
              onClick={handleBeginActiveDrill}
              className="inline-flex items-center gap-2 rounded-lg bg-forge-500 px-4 py-2.5 text-sm font-bold text-dark-950 shadow-lg shadow-forge-500/20 transition-colors hover:bg-forge-400"
            >
              <Play className="h-4 w-4 fill-current" />
              Begin active drill
              <span className="ml-1 hidden items-center gap-1 text-[10px] font-normal text-dark-950/70 sm:inline-flex">
                <Eye className="h-3 w-3" /> VisionAudioForge
              </span>
            </button>
          </div>
        )
      )}

      {/* Drill Streak Widget */}
      <DrillStreakWidget />

      {/* 7. Session Fatigue Bar */}
      <SessionFatigueBar sessionStartTime={session.isActive ? sessionStart : null} />

      {/* Main Layout: 3-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Drill Queue */}
        <div className="lg:col-span-3">
          <DrillQueue queue={queue} currentDrill={currentDrill} />
        </div>

        {/* Center: Active Drill Zone */}
        <div className="lg:col-span-6">
          {currentDrill ? (
            <div className="space-y-4">
              <DrillRunner
                drill={currentDrill}
                onCompleteRep={() => completeRep(true)}
                onSkip={skipDrill}
                onStart={startDrill}
                onEnd={endSession}
                onNext={nextDrill}
                isActive={session.isActive}
                successCount={successCount}
                failCount={failCount}
              />
              {/* 3. InputLab Telemetry */}
              <InputLabPanel drillsCompleted={completedDrillCount} />
            </div>
          ) : (
            <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-12 text-center">
              <Swords className="w-12 h-12 text-dark-600 mx-auto mb-3" />
              <p className="text-dark-400">No drills available</p>
              <p className="text-sm text-dark-600 mt-1">
                Check back later for new training assignments
              </p>
            </div>
          )}
        </div>

        {/* Right: Skill Progress + Transfer Panel */}
        <div className="lg:col-span-3 space-y-4">
          <SkillProgress skills={skillProgress} />
          {/* 1. TransferAI Competition Readiness */}
          <TransferReadinessPanel skills={skillProgress} />
          {/* TransferAI Readiness — Lab vs Live Gap */}
          <TransferAIReadiness />
          {/* 9. Monthly Consistency */}
          <MonthlyConsistency />
        </div>
      </div>

      {/* 2. LoopAI Debrief Modal */}
      <DrillDebriefModal
        open={showDebrief}
        onClose={() => { setShowDebrief(false); clearLastCompleted(); }}
        onContinue={() => { setShowDebrief(false); clearLastCompleted(); nextDrill(); }}
        onEndSession={() => { setShowDebrief(false); clearLastCompleted(); endSession(); }}
        drillName={lastCompletedDrill?.name ?? currentDrill?.name ?? ''}
        score={lastCompletedDrill?.successRate ?? currentDrill?.successRate ?? 0}
        previousScore={72}
        skillGain="Read Speed +3 pts"
        twinUpdate="PlayerTwin updated: coverage read baseline raised from 62 to 65"
        nextDrillName={queue[0]?.name ?? null}
      />

      {/* Enhanced Post-Drill Debrief with improvements + focus areas */}
      <PostDrillDebrief
        open={showPostDebrief}
        onClose={() => { setShowPostDebrief(false); clearLastCompleted(); }}
        onContinue={() => { setShowPostDebrief(false); clearLastCompleted(); nextDrill(); }}
        onEndSession={() => { setShowPostDebrief(false); clearLastCompleted(); endSession(); }}
        drillName={lastCompletedDrill?.name ?? currentDrill?.name ?? ''}
        score={lastCompletedDrill?.successRate ?? currentDrill?.successRate ?? 0}
        previousScore={72}
        improvements={[
          'Coverage read speed improved +3 pts',
          'Pre-snap recognition accuracy up from 62% to 68%',
          'Route identification under pressure now at 71%',
        ]}
        focusAreas={[
          'Blitz recognition still below competition threshold',
          'Audible speed needs 0.3s improvement for live play',
        ]}
        twinUpdate="PlayerTwin updated: coverage read baseline raised from 62 to 65"
        nextDrillName={queue[0]?.name ?? null}
      />

      <PreDrillBriefModal
        open={briefOpen}
        drill={currentDrill}
        onStart={handleStartActiveDrill}
        onCancel={() => setBriefOpen(false)}
      />

      <DrillDebrief
        open={debriefData !== null}
        drill={debriefData?.drill ?? null}
        debrief={debriefData?.debrief ?? null}
        reps={debriefData?.reps ?? []}
        nextDrill={queue[0] ?? null}
        onNext={handleDebriefNext}
        onEnd={handleDebriefEnd}
      />
    </div>
  );
}

export default function DrillsPage() {
  return (
    <Suspense fallback={null}>
      <DrillsPageInner />
    </Suspense>
  );
}

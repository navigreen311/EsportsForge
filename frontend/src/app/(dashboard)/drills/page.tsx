'use client';

import { useState } from 'react';
import { Swords } from 'lucide-react';
import { useDrills } from '@/hooks/useDrills';
import DrillRunner from '@/components/drills/DrillRunner';
import DrillQueue from '@/components/drills/DrillQueue';
import SkillProgress from '@/components/drills/SkillProgress';
import DrillSummary from '@/components/drills/DrillSummary';
import TransferReadinessPanel from '@/components/drills/TransferReadinessPanel';
import InputLabPanel from '@/components/drills/InputLabPanel';
import SessionFatigueBar from '@/components/drills/SessionFatigueBar';
import DrillDebriefModal from '@/components/drills/DrillDebriefModal';
import { DrillStreak } from '@/components/drills/DrillStreakTracker';
import { MonthlyConsistency } from '@/components/drills/DrillStreakTracker';

export default function DrillsPage() {
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
  } = useDrills();

  const [sessionStart] = useState<Date | null>(() => new Date());
  const [showDebrief, setShowDebrief] = useState(false);

  const completedDrillCount = session.completedDrills.length;

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
                onCompleteRep={completeRep}
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
          {/* 9. Monthly Consistency */}
          <MonthlyConsistency />
        </div>
      </div>

      {/* 2. LoopAI Debrief Modal */}
      <DrillDebriefModal
        open={showDebrief}
        onClose={() => setShowDebrief(false)}
        onContinue={() => { setShowDebrief(false); nextDrill(); }}
        onEndSession={() => { setShowDebrief(false); endSession(); }}
        drillName={currentDrill?.name ?? ''}
        score={currentDrill?.successRate ?? 0}
        previousScore={72}
        skillGain="Read Speed +3 pts"
        twinUpdate="PlayerTwin updated: coverage read baseline raised from 62 to 65"
        nextDrillName={queue[0]?.name ?? null}
      />
    </div>
  );
}

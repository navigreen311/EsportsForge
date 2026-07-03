'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Swords, Shield, X as XIcon, Info } from 'lucide-react';
import api from '@/lib/api';
import { useDrills } from '@/hooks/useDrills';
import { useVisionEvents } from '@/hooks/useVisionEvents';
import { useDrillLabAutoRep } from '@/hooks/useDrillLabAutoRep';
import { useActiveArsenalTitle, type WeaponSide } from '@/hooks/useArsenal';
import {
  SideToggle,
  DEFENSE_LABEL_BY_TITLE,
} from '@/components/shared/SideToggle';
import { DEFENSIVE_DRILLS_BY_TITLE } from '@/lib/drills/defensiveDrills';
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
import { WatchingPageHint } from '@/components/global/WatchingPageHint';

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
    lastCompletedDrill,
    clearLastCompleted,
  } = useDrills();

  const [sessionStart] = useState<Date | null>(() => new Date());
  const [showDebrief, setShowDebrief] = useState(false);
  const [showPostDebrief, setShowPostDebrief] = useState(false);
  const [side, setSide] = useState<WeaponSide>('offense');
  const titleId = useActiveArsenalTitle();
  const defensiveDrills = DEFENSIVE_DRILLS_BY_TITLE[titleId] ?? [];

  // Phase 1a: vision-driven rep auto-completion (event-display-only), flag-gated
  // (NEXT_PUBLIC_VAF_DRILL_LAB_ENABLED). Real per-user flag infra lands when
  // widening past the solo founder, not now.
  const vafFlagOn = process.env.NEXT_PUBLIC_VAF_DRILL_LAB_ENABLED === 'true';
  // Session-id is provisioned by the backend broker (browser -> backend -> core),
  // replacing the earlier NEXT_PUBLIC_VAF_SESSION_ID stub. Runs once when the
  // flag is on; until a real session_id lands, `enabled` stays false so nothing
  // connects to a fake session.
  const [vafSession, setVafSession] = useState<{ sessionId: string; token: string } | null>(null);
  useEffect(() => {
    if (!vafFlagOn) return;
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.post('/visionaudio/sessions/start');
        if (!cancelled) setVafSession({ sessionId: data.session_id, token: data.token });
      } catch {
        // Broker unavailable / disabled server-side — stay on the manual path.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [vafFlagOn]);
  const { lastEvent: vafLastEvent, connected: vafConnected } = useVisionEvents({
    sessionId: vafSession?.sessionId ?? null,
    token: vafSession?.token ?? null,
    eventType: 'FORMATION_LOCKED',
    enabled: vafFlagOn && !!vafSession,
  });
  // Map play-call-screen → rep (§4c): one FORMATION_LOCKED = one rep, deduped
  // by event_id. Manual completeRep (via DrillRunner) stays the flag-off path.
  useDrillLabAutoRep({ lastEvent: vafLastEvent, onRep: () => completeRep(true) });

  const completedDrillCount = session.completedDrills.length;

  // Banner reader: priority/focus/filter/dailyForgeDrill query params
  const searchParams = useSearchParams();
  const priorityParam = searchParams?.get('priority') ?? null;
  const focusParam = searchParams?.get('focus') ?? null;
  const filterParam = searchParams?.get('filter') ?? null;
  const dailyForgeDrill = searchParams?.get('dailyForgeDrill') ?? null;

  let bannerMessage: string | null = null;
  if (focusParam === 'execution-gap') {
    bannerMessage =
      'Closing the gap — Coverage Reads 91% in drills, only 54% in ranked games. These reps build the transfer.';
  } else if (focusParam === 'transfer-gap') {
    bannerMessage =
      'TransferAI: Your skills are not transferring under pressure. These drills simulate live game pressure conditions.';
  } else if (priorityParam) {
    bannerMessage = `Fixing: ${priorityParam} — your #1 priority`;
  } else if (dailyForgeDrill) {
    bannerMessage = `Today's Daily Forge drill: ${dailyForgeDrill}`;
  } else if (filterParam) {
    bannerMessage = `Filter: ${filterParam}`;
  }

  const [bannerDismissed, setBannerDismissed] = useState(false);
  // Re-show banner if the underlying message changes
  useEffect(() => {
    setBannerDismissed(false);
  }, [bannerMessage]);

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
      {/* Contextual banner — driven by query params */}
      {bannerMessage && !bannerDismissed && (
        <div className="flex items-start gap-3 rounded-xl border border-forge-500/30 bg-forge-500/10 px-4 py-3">
          <Info className="mt-0.5 h-4 w-4 flex-shrink-0 text-forge-300" />
          <p className="flex-1 text-sm text-forge-100">{bannerMessage}</p>
          <button
            type="button"
            aria-label="Dismiss"
            onClick={() => setBannerDismissed(true)}
            className="flex-shrink-0 rounded-md p-1 text-forge-300 transition-colors hover:bg-forge-500/20 hover:text-forge-100"
          >
            <XIcon className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

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

        {/* Watching status + Session Progress + Streak */}
        <div className="flex items-start gap-3">
          <WatchingPageHint
            pageName="Drill Lab"
            onHint="Watching Drill Lab — auto-tracking reps when frames flow"
            offHint="Enable Watching for auto-rep tracking"
            className="hidden md:inline-flex"
          />
          <div className="text-right hidden md:block space-y-1">
            <p className="text-sm text-dark-400">Session Progress</p>
            <p className="text-lg font-bold font-mono text-dark-100">
              {totalReps}/{totalTargetReps}{' '}
              <span className="text-sm text-dark-500 font-normal">reps</span>
            </p>
            {/* Phase 1a Day 3: vision status + latest formation (display-only) */}
            {vafFlagOn && (
              <p className="text-xs text-dark-500">
                Vision: {vafConnected ? 'connected' : 'off'}
                {vafSession ? ` · ${vafSession.sessionId}` : ''}
                {vafLastEvent?.payload.offensive_formation
                  ? ` · ${vafLastEvent.payload.offensive_formation}`
                  : ''}
              </p>
            )}
            {/* 9. Drill Streak */}
            <DrillStreak />
          </div>
        </div>
      </div>

      {/* Offense / Defense toggle */}
      <div className="flex items-center justify-between">
        <SideToggle
          side={side}
          onChange={setSide}
          offenseLabel="Offense Drills"
          defenseLabel={
            DEFENSE_LABEL_BY_TITLE[titleId]
              ? `${DEFENSE_LABEL_BY_TITLE[titleId]} Drills`
              : 'Defense Drills'
          }
          disabledSide={defensiveDrills.length === 0 ? 'defense' : undefined}
        />
        <p className="text-[11px] text-dark-500">
          {side === 'defense'
            ? 'Coverage, pressure, jockeying, parrying — defensive execution reps'
            : 'Reads, throws, dribble moves — offensive execution reps'}
        </p>
      </div>

      {side === 'defense' && (
        <div className="rounded-xl border border-sky-500/30 bg-sky-500/5 p-5">
          <div className="mb-4 flex items-center gap-2">
            <Shield className="h-4 w-4 text-sky-300" />
            <h3 className="text-sm font-bold text-sky-200">
              Defensive Drill Queue
            </h3>
            <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2 py-0.5 text-[10px] text-sky-300">
              {defensiveDrills.length} drills
            </span>
          </div>
          {defensiveDrills.length === 0 ? (
            <p className="rounded-md border border-dashed border-dark-700 bg-dark-800/40 p-4 text-center text-xs text-dark-500">
              No defensive drills for this title yet.
            </p>
          ) : (
            <ul className="space-y-2">
              {defensiveDrills.map((d) => (
                <li
                  key={d.id}
                  className="flex items-center gap-3 rounded-lg bg-dark-900/60 p-3"
                >
                  <div className="flex h-8 w-12 flex-shrink-0 items-center justify-center rounded-md border border-sky-500/30 bg-sky-500/10 font-mono text-xs font-bold text-sky-300">
                    {d.impactRank.toFixed(1)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-bold text-dark-100">
                      {d.name}
                    </p>
                    <p className="truncate text-[11px] text-dark-400">
                      {d.description}
                    </p>
                  </div>
                  <div className="flex flex-shrink-0 items-center gap-3 text-[11px] text-dark-500">
                    <span>{d.reps} reps</span>
                    <span>{d.durationMinutes}m</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-3 text-[11px] text-dark-500">
            Defensive ImpactRank scoring runs on the same engine as offense
            once the DefensivePriority pipeline lands. These IRs are
            illustrative.
          </p>
        </div>
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
    </div>
  );
}

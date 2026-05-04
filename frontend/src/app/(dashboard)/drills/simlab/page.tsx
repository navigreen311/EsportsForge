/**
 * SimLab — Scenario Sandbox.
 * Pre-built and custom scenario simulations with decision trees,
 * rep tracking, and results analysis.
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useWeapon, useActiveArsenalTitle } from '@/hooks/useArsenal';
import {
  FlaskConical,
  Play,
  RotateCcw,
  ChevronRight,
  Target,
  Clock,
  TrendingUp,
  Zap,
  CheckCircle2,
  XCircle,
  Users,
  Volume2,
  VolumeX,
  Eye,
} from 'lucide-react';
import { VoiceForgeService } from '@/lib/services/voiceforge';
import { useArsenalVoice, toneSpeed } from '@/lib/arsenal/voiceSettings';
import {
  VisionAudioForgeService,
  type DrillMonitoringHandle,
  type FrameAnalysis,
} from '@/lib/services/visionaudioforge';
import { getSimLabDetectionConfig } from '@/lib/drills/drillDetectionConfigs';
import { WatchingIndicator } from '@/components/session/WatchingIndicator';
import { CaptureSourceModal } from '@/components/session/CaptureSourceModal';
import { useUIStore } from '@/lib/store';
import {
  SideToggle,
  DEFENSE_LABEL_BY_TITLE,
} from '@/components/shared/SideToggle';
import type { WeaponSide } from '@/hooks/useArsenal';

// --- Mock Data ---

interface Scenario {
  id: string;
  name: string;
  description: string;
  icon: string;
  difficulty: 'easy' | 'medium' | 'hard';
}

const SCENARIOS: Scenario[] = [
  { id: '3rd-medium', name: '3rd & Medium', description: '3rd & 5-7, between the 20s', icon: '3️⃣', difficulty: 'medium' },
  { id: '2min-drill', name: '2-Minute Drill', description: 'Down 3, own 25, 2:00 left', icon: '⏱️', difficulty: 'hard' },
  { id: 'red-zone', name: 'Red Zone', description: '1st & Goal from the 8', icon: '🔴', difficulty: 'medium' },
  { id: 'backed-up', name: 'Backed-Up', description: '1st & 10 own 3-yard line', icon: '🧱', difficulty: 'hard' },
  { id: '4th-short', name: '4th & Short', description: '4th & 1, midfield', icon: '4️⃣', difficulty: 'easy' },
  { id: 'protect-lead', name: 'Protecting Lead', description: 'Up 7, opponent ball, 3:00 left', icon: '🛡️', difficulty: 'medium' },
  { id: 'down-7-late', name: 'Down 7 Late', description: 'Down 7, own 35, 1:20 left', icon: '🚨', difficulty: 'hard' },
  { id: 'bunch-trips', name: 'Defending Bunch/Trips', description: 'Opponent in 3x1, pick best coverage', icon: '👁️', difficulty: 'medium' },
];

// Defensive SimLab scenarios — keyed by title because the situations the
// player is *defending* differ enormously per genre. Where a title doesn't
// have a structured defensive sandbox (Golf course management is itself
// defensive — it's covered on the offense side), the entry is omitted and
// the side toggle disables 'defense' for that title.
const DEFENSIVE_SCENARIOS: Record<string, Scenario[]> = {
  'madden-26': [
    { id: '3rd-and-long-stop', name: '3rd & Long Stop', description: '3rd & 10+, opponent in shotgun', icon: '🛑', difficulty: 'hard' },
    { id: 'red-zone-defense', name: 'Red Zone Defense', description: 'Defend goal-line stand from the 5', icon: '🥅', difficulty: 'hard' },
    { id: '2-min-defense', name: '2-Minute Defense', description: 'Up 3, opponent ball, 2:00 left', icon: '⏱️', difficulty: 'medium' },
    { id: 'protecting-lead', name: 'Protecting a Lead', description: 'Up 7, opponent driving, 4:00 Q4', icon: '🛡️', difficulty: 'medium' },
    { id: 'turnover-needed', name: 'Turnover Needed', description: 'Down 10, must get the ball back', icon: '🎯', difficulty: 'hard' },
  ],
  'cfb-26': [
    { id: 'option-defense', name: 'Option Defense', description: 'Triple option from under center', icon: '🛡️', difficulty: 'hard' },
    { id: 'rpo-defense', name: 'RPO Defense', description: 'Quick-game RPO concept', icon: '🛡️', difficulty: 'medium' },
    { id: 'red-zone-d-cfb', name: 'Red Zone Defense', description: '1st & Goal from the 8', icon: '🥅', difficulty: 'medium' },
    { id: 'two-min-d-cfb', name: '2-Minute Defense', description: 'Up 3, opponent at midfield', icon: '⏱️', difficulty: 'medium' },
  ],
  'nba-2k26': [
    { id: 'pnr-defense', name: 'PNR Defense', description: 'Pull-up shooter coming off ball-screen', icon: '🛡️', difficulty: 'medium' },
    { id: 'isolation-defense', name: 'Isolation Defense', description: 'Top-of-key iso, no help', icon: '🥅', difficulty: 'medium' },
    { id: 'end-clock-defense', name: 'End of Clock Defense', description: 'Shot clock under 8s, contest only', icon: '⏱️', difficulty: 'hard' },
    { id: 'inbound-defense', name: 'Inbound Defense', description: 'Sideline out with 5s left', icon: '🚫', difficulty: 'easy' },
    { id: 'fast-break-defense', name: 'Fast Break Defense', description: '3-on-2 transition', icon: '🏃', difficulty: 'medium' },
  ],
  'eafc-26': [
    { id: 'counter-defense', name: 'Counter Attack Defense', description: '2-on-2 break against you', icon: '🛡️', difficulty: 'hard' },
    { id: 'set-piece-defense', name: 'Set Piece Defense', description: 'Corner to far post', icon: '🥅', difficulty: 'medium' },
    { id: '1v1-defense', name: '1v1 Defending', description: 'Solo defender vs. dribbler at top of box', icon: '🥊', difficulty: 'medium' },
    { id: 'high-press-trigger', name: 'High Press Trigger', description: 'Press when their CB has it', icon: '⚡', difficulty: 'easy' },
    { id: 'cross-defense', name: 'Cross Defense', description: 'Wide cross from the byline', icon: '↗️', difficulty: 'medium' },
  ],
  'mlb-26': [
    { id: 'two-strike-pitch', name: 'Two-Strike Sequence', description: 'Pull-hitter, 0-2 count', icon: '⚾', difficulty: 'medium' },
    { id: 'shift-defense', name: 'Shift Setup', description: 'Defend pull-heavy lefty', icon: '🛡️', difficulty: 'easy' },
    { id: 'first-and-third', name: '1st & 3rd Defense', description: 'Runner steal + tag situation', icon: '🥎', difficulty: 'hard' },
    { id: 'bases-loaded', name: 'Bases Loaded', description: '0 outs, slugger up', icon: '🥅', difficulty: 'hard' },
  ],
  'warzone': [
    { id: 'hold-position', name: 'Hold Position', description: 'High ground, 2 squads incoming', icon: '🛡️', difficulty: 'medium' },
    { id: 'rotation-defense', name: 'Defensive Rotation', description: 'Rotate to next zone under fire', icon: '🏃', difficulty: 'hard' },
    { id: '1v3-defense', name: '1v3 Defense', description: 'Last man, must reset and trade', icon: '🥊', difficulty: 'hard' },
    { id: 'building-defense', name: 'Building Defense', description: 'Hold top floor, stairwell only entry', icon: '🏢', difficulty: 'medium' },
    { id: 'anti-rush', name: 'Anti-Rush', description: 'Squad pushing your position', icon: '⚡', difficulty: 'easy' },
  ],
  'fortnite': [
    { id: 'box-defense', name: 'Box Defense', description: 'Opponent edit-pushing your box', icon: '📦', difficulty: 'medium' },
    { id: 'high-ground-retake', name: 'High Ground Retake', description: 'Retake high without dying', icon: '⛰️', difficulty: 'hard' },
    { id: 'anti-rush-fn', name: 'Anti-Rush', description: 'Opponent rotating through your build', icon: '⚡', difficulty: 'easy' },
    { id: 'storm-defense', name: 'Storm Defense', description: 'Last 30s rotation through gas', icon: '🌪️', difficulty: 'medium' },
  ],
  'ufc-5': [
    { id: 'takedown-defense', name: 'Takedown Defense', description: 'Wrestler shooting at you', icon: '🛡️', difficulty: 'hard' },
    { id: 'submission-defense', name: 'Submission Defense', description: 'Caught in a guillotine', icon: '🥋', difficulty: 'hard' },
    { id: 'counter-strike-setup', name: 'Counter Strike Setup', description: 'Slip the jab, fire the cross', icon: '🥊', difficulty: 'medium' },
    { id: 'clinch-defense', name: 'Clinch Defense', description: 'Pinned to the cage', icon: '🤼', difficulty: 'medium' },
    { id: 'wall-defense', name: 'Wall Defense', description: 'Back to the cage, must exit', icon: '🧱', difficulty: 'easy' },
  ],
  'pga-2k25': [
    { id: 'lay-up-decision', name: 'Lay Up Decision', description: 'Hazard 240 out, par 5', icon: '🛡️', difficulty: 'easy' },
    { id: 'wind-defense', name: 'Wind Defense', description: '15mph crosswind, narrow fairway', icon: '💨', difficulty: 'medium' },
    { id: 'bogey-recovery', name: 'Bogey Recovery', description: 'In trees, 180 to green', icon: '🌳', difficulty: 'medium' },
    { id: 'pressure-putt', name: 'Pressure Putt', description: '6ft for par, downhill', icon: '⛳', difficulty: 'medium' },
  ],
  'undisputed': [
    { id: 'shoulder-roll-counter', name: 'Shoulder Roll Counter', description: 'Right-hand-heavy opponent', icon: '🛡️', difficulty: 'hard' },
    { id: 'parry-counter', name: 'Parry Counter', description: 'Time the parry, fire the cross', icon: '🥊', difficulty: 'medium' },
    { id: 'guard-management', name: 'Guard Management', description: 'Opponent body-shot heavy', icon: '🛡️', difficulty: 'medium' },
    { id: 'corner-escape', name: 'Corner Escape', description: 'Cornered, taking shots', icon: '🚪', difficulty: 'easy' },
  ],
  'video-poker': [
    { id: 'loss-limit', name: 'Loss Limit Discipline', description: 'Down 30%, 5 hands losing in a row', icon: '🛡️', difficulty: 'easy' },
    { id: 'variance-tolerance', name: 'Variance Tolerance', description: 'Cold streak, EV says continue', icon: '📉', difficulty: 'medium' },
    { id: 'optimal-hold', name: 'Optimal Hold Test', description: 'Tricky 4-to-flush-vs-pair decision', icon: '🃏', difficulty: 'medium' },
  ],
};

const TITLE_ALIAS: Record<string, string> = {
  // The frontend store uses condensed IDs; defensive scenarios index by
  // canonical hyphenated IDs.
  madden26: 'madden-26',
  cfb26: 'cfb-26',
  nba2k26: 'nba-2k26',
  fc26: 'eafc-26',
  mlbtheshow26: 'mlb-26',
  ufc5: 'ufc-5',
  pga2k25: 'pga-2k25',
  videopoker: 'video-poker',
};

const MOCK_OPPONENTS = [
  'xViper_Elite',
  'ColdRead99',
  'BlitzKing_',
  'SchemeMaster',
  'LabRat420',
  'ZoneHawk',
  'PressureKing',
];

interface DecisionNode {
  condition: string;
  action: string;
  children?: DecisionNode[];
}

const DECISION_TREE: DecisionNode[] = [
  {
    condition: 'Defense shows Cover 3',
    action: 'Attack seam with TE',
    children: [
      { condition: 'LB drops under seam', action: 'Hit crosser underneath' },
      { condition: 'LB blitzes', action: 'Hot route — slant to vacated zone' },
    ],
  },
  {
    condition: 'Defense shows Man/Press',
    action: 'Motion to confirm',
    children: [
      { condition: 'DB follows motion', action: 'Run out route or corner' },
      { condition: 'Zone exchange', action: 'Actually zone — run levels concept' },
    ],
  },
  {
    condition: 'Defense shows Blitz look',
    action: 'Check to max protect + hot',
    children: [
      { condition: 'They bring 6+', action: 'Hot slant to pressure side' },
      { condition: 'They bail out', action: 'Take what defense gives — dump off' },
    ],
  },
];

interface RepResult {
  id: number;
  correct: boolean;
  timeMs: number;
  scenario: string;
  /** True when the rep was filled in by VisionAudioForge auto-detection. */
  autoDetected?: boolean;
  /** Vision-model confidence 0–100 — anything below 50 is flagged amber. */
  confidence?: number;
  reason?: string;
}

export default function SimLabPage() {
  const searchParams = useSearchParams();
  const weaponId = searchParams?.get('weapon') ?? null;
  const { data: preloadedWeapon } = useWeapon(weaponId);
  const voice = useArsenalVoice();
  const arsenalTitle = useActiveArsenalTitle();
  const integrityMode = useUIStore((s) => s.currentMode);
  const [side, setSide] = useState<WeaponSide>('offense');
  const titleKey = TITLE_ALIAS[arsenalTitle] ?? arsenalTitle;
  const defensiveScenarios = DEFENSIVE_SCENARIOS[titleKey] ?? [];
  const scenarioList: Scenario[] =
    side === 'defense' ? defensiveScenarios : SCENARIOS;
  const defenseAvailable = defensiveScenarios.length > 0;
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [selectedOpponent, setSelectedOpponent] = useState(MOCK_OPPONENTS[0]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [voiceCoaching, setVoiceCoaching] = useState(true);
  const [watching, setWatching] = useState(false);
  const [showCaptureSourceModal, setShowCaptureSourceModal] = useState(false);
  const watchHandleRef = useRef<DrillMonitoringHandle | null>(null);
  const [reps, setReps] = useState<RepResult[]>([
    { id: 1, correct: true, timeMs: 2400, scenario: '3rd & Medium' },
    { id: 2, correct: true, timeMs: 1800, scenario: '3rd & Medium' },
    { id: 3, correct: false, timeMs: 3200, scenario: 'Red Zone' },
    { id: 4, correct: true, timeMs: 2100, scenario: '2-Minute Drill' },
    { id: 5, correct: false, timeMs: 4100, scenario: 'Down 7 Late' },
  ]);

  // Custom scenario builder state
  const [customState, setCustomState] = useState({
    score: 'Tied',
    time: '5:00 Q4',
    down: '3rd',
    distance: '6',
    fieldPosition: 'Own 40',
    tendency: 'Zone Heavy',
  });

  const speakIfEnabled = (line: string) => {
    if (!voiceCoaching) return;
    if (!voice.enabled || !VoiceForgeService.isAvailable()) return;
    VoiceForgeService.speak(line, {
      interruptCurrent: true,
      speed: toneSpeed(voice.tone),
    });
  };

  const coachAfterRep = (correct: boolean, totalReps: number, accuracyPct: number) => {
    if (totalReps === 1) {
      speakIfEnabled(
        `Rep 1 complete. ${correct ? 'Clean read.' : 'Missed it — focus on the pre-snap look.'}`
      );
      return;
    }
    if (totalReps === 5) {
      speakIfEnabled(
        accuracyPct >= 80
          ? `5 reps in. ${accuracyPct} percent accuracy. Strong reads — stay consistent.`
          : `5 reps in. ${accuracyPct} percent accuracy. Focus on the pre-snap look — read safeties first.`
      );
      return;
    }
    if (totalReps === 10) {
      speakIfEnabled(
        `Session complete. ${accuracyPct} percent accuracy across 10 reps. LoopAI has updated your profile.`
      );
      return;
    }
    speakIfEnabled(
      correct
        ? `Rep ${totalReps}. Good execution.`
        : `Rep ${totalReps}. Review the read.`
    );
  };

  const runSimulation = () => {
    setIsSimulating(true);
    setShowResult(false);
    setTimeout(() => {
      setIsSimulating(false);
      setShowResult(true);
      const correct = Math.random() > 0.35;
      const timeMs = 1500 + Math.random() * 3000;
      setReps((prev) => {
        const updated = [
          {
            id: prev.length + 1,
            correct,
            timeMs: Math.round(timeMs),
            scenario: selectedScenario?.name ?? 'Custom',
          },
          ...prev,
        ];
        const acc = Math.round(
          (updated.filter((r) => r.correct).length / updated.length) * 100
        );
        coachAfterRep(correct, updated.length, acc);
        return updated;
      });
    }, 1500);
  };

  // -----------------------------------------------------------------------
  // Watching mode — VisionAudioForge auto-detects each rep
  // -----------------------------------------------------------------------

  const handleRepDetected = (analysis: FrameAnalysis) => {
    // Skip when the model could not commit either way.
    if (analysis.success === null) return;
    setReps((prev) => {
      const next = [
        {
          id: prev.length + 1,
          correct: analysis.success === true,
          timeMs: 0,
          scenario:
            preloadedWeapon?.name ?? selectedScenario?.name ?? 'Custom',
          autoDetected: true,
          confidence: analysis.confidence,
          reason: analysis.reason,
        },
        ...prev,
      ];
      const acc = Math.round(
        (next.filter((r) => r.correct).length / next.length) * 100
      );
      coachAfterRep(analysis.success === true, next.length, acc);
      return next;
    });
  };

  const startWatching = async () => {
    if (!VisionAudioForgeService.getCaptureSource()) {
      setShowCaptureSourceModal(true);
      return;
    }
    const available = await VisionAudioForgeService.isAvailable();
    if (!available) {
      speakIfEnabled(
        'VisionAudioForge is offline. Use Run Scenario to mark reps manually.'
      );
      return;
    }

    const config = getSimLabDetectionConfig(
      selectedScenario?.id,
      preloadedWeapon?.name,
      preloadedWeapon?.formation ?? undefined,
      preloadedWeapon?.play_name ?? undefined
    );

    watchHandleRef.current = VisionAudioForgeService.startDrillMonitoring({
      mode: 'simlab',
      titleId: arsenalTitle,
      scenarioId: selectedScenario?.id,
      weaponId: preloadedWeapon?.id,
      weaponName: preloadedWeapon?.name,
      formation: preloadedWeapon?.formation ?? undefined,
      playName: preloadedWeapon?.play_name ?? undefined,
      detectionConfig: config,
      onRepDetected: handleRepDetected,
    });
    setWatching(true);
    speakIfEnabled(
      'VisionAudioForge is now watching your screen. Go to your game and execute the scenario. I will detect each rep automatically.'
    );
  };

  const stopWatching = () => {
    watchHandleRef.current?.stop();
    watchHandleRef.current = null;
    setWatching(false);
  };

  useEffect(() => {
    return () => watchHandleRef.current?.stop();
  }, []);

  const accuracy = reps.length > 0
    ? Math.round((reps.filter((r) => r.correct).length / reps.length) * 100)
    : 0;
  const avgTime = reps.length > 0
    ? Math.round(reps.reduce((a, r) => a + r.timeMs, 0) / reps.length)
    : 0;

  return (
    <div className="space-y-6">
      {/* Arsenal preload notice */}
      {preloadedWeapon && (
        <div className="flex items-center gap-3 rounded-xl border border-forge-500/30 bg-emerald-950/20 px-4 py-3">
          <Zap className="h-5 w-5 flex-shrink-0 text-forge-400" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold text-dark-100">
              SimLab scenario preloaded for {preloadedWeapon.name}
            </p>
            <p className="text-[11px] text-dark-400">{preloadedWeapon.when_to_use}</p>
          </div>
        </div>
      )}

      {/* TOURNAMENT INTEGRITY NOTICE */}
      {integrityMode === 'tournament' && (
        <div className="rounded-lg border border-sky-500/30 bg-sky-500/10 px-4 py-2 text-xs text-sky-200">
          Tournament mode active. Practice monitoring is allowed between rounds —
          this is offline training, not live competitive play.
        </div>
      )}

      {/* HEADER */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-forge-500/15">
            <FlaskConical className="h-5 w-5 text-forge-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-dark-50">SimLab</h1>
            <p className="text-sm text-dark-400">Scenario Sandbox &mdash; drill specific situations</p>
          </div>
        </div>
        <SideToggle
          side={side}
          onChange={(s) => {
            setSide(s);
            setSelectedScenario(null);
            setShowResult(false);
          }}
          defenseLabel={DEFENSE_LABEL_BY_TITLE[titleKey] ?? 'Defense'}
          disabledSide={defenseAvailable ? undefined : 'defense'}
        />
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-dark-800 px-3 py-1.5 text-xs text-dark-300">
            <span className="text-dark-500">Reps today:</span> <span className="font-semibold text-dark-100">{reps.length}</span>
          </div>
          <div className="rounded-lg bg-dark-800 px-3 py-1.5 text-xs text-dark-300">
            <span className="text-dark-500">Accuracy:</span> <span className="font-semibold text-forge-400">{accuracy}%</span>
          </div>
          <button
            type="button"
            onClick={() => setVoiceCoaching((v) => !v)}
            className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors ${
              voiceCoaching
                ? 'border-forge-500/40 bg-forge-500/10 text-forge-300 hover:bg-forge-500/20'
                : 'border-dark-700 bg-dark-800 text-dark-300 hover:bg-dark-700'
            }`}
            title={voiceCoaching ? 'Disable rep-by-rep voice coaching' : 'Enable rep-by-rep voice coaching'}
          >
            {voiceCoaching ? <Volume2 className="h-3.5 w-3.5" /> : <VolumeX className="h-3.5 w-3.5" />}
            Voice: {voiceCoaching ? 'ON' : 'OFF'}
          </button>
          {!watching ? (
            <button
              type="button"
              onClick={startWatching}
              className="inline-flex items-center gap-1.5 rounded-lg border border-forge-500/40 bg-forge-500/10 px-3 py-1.5 text-xs font-bold text-forge-300 hover:bg-forge-500/20"
              title="Let VisionAudioForge auto-detect each rep from your screen"
            >
              <Eye className="h-3.5 w-3.5" />
              Start Watching
            </button>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-lg border border-forge-500/40 bg-forge-500/10 px-3 py-1.5 text-xs font-bold text-forge-300">
              <Eye className="h-3.5 w-3.5 animate-pulse" />
              Watching…
            </span>
          )}
        </div>
      </div>

      {watching && (
        <div className="space-y-2">
          <WatchingIndicator
            isWatching={watching}
            onStop={stopWatching}
            mode="simlab"
            detail={preloadedWeapon?.name ?? selectedScenario?.name ?? 'Custom scenario'}
          />
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-dark-400">
            <span className="text-dark-500">Manual override:</span>
            <button
              type="button"
              onClick={() =>
                handleRepDetected({
                  playInProgress: false,
                  repCompleted: true,
                  success: true,
                  coverageDetected: null,
                  playDetected: null,
                  executionQuality: 'clean',
                  confidence: 100,
                  reason: 'Manually marked success',
                })
              }
              className="inline-flex items-center gap-1 rounded-md border border-forge-500/30 bg-forge-500/10 px-2 py-0.5 font-medium text-forge-300 hover:bg-forge-500/20"
            >
              ✓ Mark Success
            </button>
            <button
              type="button"
              onClick={() =>
                handleRepDetected({
                  playInProgress: false,
                  repCompleted: true,
                  success: false,
                  coverageDetected: null,
                  playDetected: null,
                  executionQuality: 'poor',
                  confidence: 100,
                  reason: 'Manually marked failed',
                })
              }
              className="inline-flex items-center gap-1 rounded-md border border-red-500/30 bg-red-500/10 px-2 py-0.5 font-medium text-red-300 hover:bg-red-500/20"
            >
              ✗ Mark Failed
            </button>
          </div>
        </div>
      )}

      <CaptureSourceModal
        open={showCaptureSourceModal}
        onClose={() => setShowCaptureSourceModal(false)}
        onSelected={() => {
          setShowCaptureSourceModal(false);
          void startWatching();
        }}
      />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* LEFT COLUMN — Scenario Selector + Custom Builder */}
        <div className="space-y-6">
          {/* SCENARIO SELECTOR */}
          <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
              <Target className="h-4 w-4 text-forge-400" /> Scenarios
            </h2>
            <div className="grid grid-cols-2 gap-2">
              {scenarioList.length === 0 && (
                <p className="col-span-2 rounded-md border border-dashed border-dark-700 bg-dark-800/40 px-3 py-3 text-center text-[11px] text-dark-500">
                  No defensive scenarios for this title yet.
                </p>
              )}
              {scenarioList.map((s) => (
                <button
                  key={s.id}
                  onClick={() => { setSelectedScenario(s); setShowResult(false); }}
                  className={`rounded-lg border px-3 py-2.5 text-left transition-all ${
                    selectedScenario?.id === s.id
                      ? 'border-forge-500/50 bg-forge-500/10'
                      : 'border-dark-700/50 bg-dark-800/60 hover:border-dark-600'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-base">{s.icon}</span>
                    <span className="text-xs font-medium text-dark-200">{s.name}</span>
                  </div>
                  <span className={`mt-1 inline-block rounded px-1.5 py-0.5 text-[10px] font-medium ${
                    s.difficulty === 'easy' ? 'bg-forge-500/15 text-forge-400' :
                    s.difficulty === 'medium' ? 'bg-amber-500/15 text-amber-400' :
                    'bg-red-500/15 text-red-400'
                  }`}>
                    {s.difficulty}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* CUSTOM SCENARIO BUILDER */}
          <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
              <Zap className="h-4 w-4 text-forge-400" /> Custom Scenario
            </h2>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(customState).map(([key, value]) => (
                <div key={key}>
                  <label className="text-[10px] uppercase tracking-wider text-dark-500 mb-1 block">
                    {key.replace(/([A-Z])/g, ' $1').trim()}
                  </label>
                  <input
                    type="text"
                    value={value}
                    onChange={(e) => setCustomState((p) => ({ ...p, [key]: e.target.value }))}
                    className="w-full rounded-lg border border-dark-700 bg-dark-800 px-2.5 py-1.5 text-xs text-dark-100 placeholder-dark-500 focus:border-forge-500/50 focus:outline-none focus:ring-1 focus:ring-forge-500/30"
                  />
                </div>
              ))}
            </div>
            <button
              onClick={() => { setSelectedScenario(null); setShowResult(false); }}
              className="mt-3 w-full rounded-lg bg-dark-800 py-2 text-xs font-medium text-dark-300 hover:bg-dark-700 transition-colors"
            >
              Use Custom State
            </button>
          </div>

          {/* OPPONENT SELECTOR */}
          <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-3">
              <Users className="h-4 w-4 text-forge-400" /> Opponent
            </h2>
            <select
              value={selectedOpponent}
              onChange={(e) => setSelectedOpponent(e.target.value)}
              className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-100 focus:border-forge-500/50 focus:outline-none focus:ring-1 focus:ring-forge-500/30"
            >
              {MOCK_OPPONENTS.map((opp) => (
                <option key={opp} value={opp}>{opp}</option>
              ))}
            </select>
          </div>
        </div>

        {/* MIDDLE COLUMN — Simulation + Decision Tree */}
        <div className="space-y-6">
          {/* SIMULATION DISPLAY */}
          <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
              <Play className="h-4 w-4 text-forge-400" /> Simulation
            </h2>

            {/* Context */}
            <div className="rounded-lg bg-dark-800/60 p-3 mb-4">
              <p className="text-xs text-dark-400 mb-1">Scenario</p>
              <p className="text-sm font-medium text-dark-100">
                {selectedScenario?.name ?? 'Custom'}: {selectedScenario?.description ?? `${customState.down} & ${customState.distance}, ${customState.fieldPosition}`}
              </p>
              <p className="text-xs text-dark-500 mt-1">vs. {selectedOpponent} ({customState.tendency})</p>
            </div>

            {/* Run Button — hidden while VisionAudioForge is auto-detecting reps */}
            {watching ? (
              <p className="rounded-lg border border-dashed border-forge-500/30 bg-forge-500/5 py-2.5 text-center text-xs text-forge-300">
                VisionAudioForge is auto-detecting reps. Manual run paused.
              </p>
            ) : (
              <button
                onClick={runSimulation}
                disabled={isSimulating}
                className="w-full rounded-lg bg-forge-500 py-2.5 text-sm font-semibold text-dark-950 hover:bg-forge-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSimulating ? 'Simulating...' : 'Run Scenario'}
              </button>
            )}

            {/* Result */}
            {showResult && (
              <div className="mt-4 space-y-3">
                <div className="rounded-lg border border-forge-500/30 bg-forge-500/5 p-3">
                  <p className="text-xs text-dark-400 mb-1">Recommended Answer</p>
                  <p className="text-sm font-medium text-dark-100">
                    Gun Trips TE — Mesh Spot (beats their tendency)
                  </p>
                </div>
                <div className="flex gap-3">
                  <div className="flex-1 rounded-lg bg-dark-800/60 p-2 text-center">
                    <p className="text-[10px] text-dark-500">Confidence</p>
                    <p className="text-sm font-bold text-forge-400">87%</p>
                  </div>
                  <div className="flex-1 rounded-lg bg-dark-800/60 p-2 text-center">
                    <p className="text-[10px] text-dark-500">Evidence</p>
                    <p className="text-sm font-bold text-dark-200">3 games</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* DECISION TREE */}
          <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
              <TrendingUp className="h-4 w-4 text-forge-400" /> Decision Tree
            </h2>
            <div className="space-y-3">
              {DECISION_TREE.map((node, i) => (
                <div key={i} className="rounded-lg bg-dark-800/60 p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-bold text-forge-400">IF</span>
                    <span className="text-xs text-dark-200">{node.condition}</span>
                  </div>
                  <div className="flex items-center gap-2 mb-2 pl-4">
                    <ChevronRight className="h-3 w-3 text-forge-500" />
                    <span className="text-xs font-medium text-dark-100">{node.action}</span>
                  </div>
                  {node.children && (
                    <div className="pl-6 space-y-1.5 border-l border-dark-700/50 ml-1">
                      {node.children.map((child, ci) => (
                        <div key={ci} className="pl-3">
                          <p className="text-[10px] text-dark-500">if {child.condition}:</p>
                          <p className="text-xs text-dark-300">&rarr; {child.action}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN — Rep Tracker + Results */}
        <div className="space-y-6">
          {/* REP TRACKER */}
          <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
              <RotateCcw className="h-4 w-4 text-forge-400" /> Rep Tracker
            </h2>
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="rounded-lg bg-dark-800/60 p-3 text-center">
                <p className="text-[10px] text-dark-500 uppercase">Total</p>
                <p className="text-lg font-bold text-dark-100">{reps.length}</p>
              </div>
              <div className="rounded-lg bg-dark-800/60 p-3 text-center">
                <p className="text-[10px] text-dark-500 uppercase">Accuracy</p>
                <p className="text-lg font-bold text-forge-400">{accuracy}%</p>
              </div>
              <div className="rounded-lg bg-dark-800/60 p-3 text-center">
                <p className="text-[10px] text-dark-500 uppercase">Avg Time</p>
                <p className="text-lg font-bold text-dark-200">{(avgTime / 1000).toFixed(1)}s</p>
              </div>
            </div>
            {/* Accuracy bar */}
            <div className="mb-2">
              <div className="flex justify-between text-[10px] text-dark-500 mb-1">
                <span>Accuracy trend</span>
                <span>{accuracy}%</span>
              </div>
              <div className="h-2 rounded-full bg-dark-800">
                <div
                  className="h-2 rounded-full bg-forge-400 transition-all"
                  style={{ width: `${accuracy}%` }}
                />
              </div>
            </div>
          </div>

          {/* RESULTS PANEL */}
          <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
              <Clock className="h-4 w-4 text-forge-400" /> Per-Rep Results
            </h2>
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {reps.map((rep) => {
                const lowConfidence =
                  rep.autoDetected && (rep.confidence ?? 0) < 50;
                return (
                  <div
                    key={rep.id}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 ${
                      lowConfidence
                        ? 'border border-amber-500/30 bg-amber-500/5'
                        : 'bg-dark-800/60'
                    }`}
                    title={rep.reason ?? undefined}
                  >
                    {rep.correct ? (
                      <CheckCircle2 className="h-4 w-4 text-forge-400 flex-shrink-0" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-dark-200 truncate">
                        {rep.scenario}
                        {rep.autoDetected && (
                          <span className="ml-1 text-[10px] text-forge-400">
                            · auto
                          </span>
                        )}
                      </p>
                      <p className="text-[10px] text-dark-500">
                        Rep #{rep.id}
                        {lowConfidence && (
                          <span className="ml-1 text-amber-400">
                            · low confidence — verify manually
                          </span>
                        )}
                      </p>
                    </div>
                    {rep.timeMs > 0 ? (
                      <span className="text-xs font-mono text-dark-400">
                        {(rep.timeMs / 1000).toFixed(1)}s
                      </span>
                    ) : null}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

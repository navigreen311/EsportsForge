/**
 * PreGameWarRoom — Full pre-game briefing component.
 * Opponent header, kill sheet, opening recommendation, tendencies,
 * TiltGuard status, meta alert, mental reset, timer, and exit.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Shield,
  Crosshair,
  Lightbulb,
  Brain,
  Zap,
  Timer,
  Heart,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  RotateCcw,
  Play,
  Pause,
  ChevronRight,
  Eye,
  Volume2,
  X,
  Clock,
  FileText,
  Smile,
  ChevronDown,
  Droplets,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useVoiceForge } from '@/hooks/useVoiceForge';
import { VoiceForgeService } from '@/lib/services/voiceforge';
import { useSessionStore } from '@/lib/sessionStore';

// ---------- Types ----------

interface KillSheetPlay {
  name: string;
  situation: string;
  successRate: number;
  notes: string;
}

interface Tendency {
  label: string;
  frequency: string;
}

interface TiltGuardStatus {
  readiness: number;
  mood: 'focused' | 'confident' | 'anxious' | 'tilted';
  fatigue: 'fresh' | 'moderate' | 'high';
}

interface Encounter {
  date: string;
  mode: string;
  result: 'W' | 'L';
  score: string;
  note: string;
}

interface OpponentData {
  gamertag: string;
  archetype: string;
  winRate: number;
  winTrend: 'up' | 'down' | 'neutral';
  lastSeen: string;
  dossierDepth: number;
  killSheet: KillSheetPlay[];
  openingRecommendation: {
    play: string;
    confidence: number;
    reason: string;
  };
  tendencies: Tendency[];
  tiltGuard: TiltGuardStatus;
  metaAlert: {
    weapon: string;
    notes: string;
  };
  mentalReset: string;
  encounters: Encounter[];
}

// ---------- Mock Data ----------
//
// Mock opponents only — the war room is a UI-shell page until the real
// opponent fetch is wired (separate architecture PR). The selector dropdown
// switches between these so the player can at least *try* changing context.

const MOCK_OPPONENT: OpponentData = {
  gamertag: 'xKillSwitch',
  archetype: 'Blitz Heavy Aggressor',
  winRate: 62,
  winTrend: 'up',
  lastSeen: '2 days ago',
  dossierDepth: 14,
  killSheet: [
    {
      name: 'Quick Slant vs Nickel Blitz',
      situation: '3rd and 7+',
      successRate: 87,
      notes: 'Hot route slot to slant, hit before blitz arrives',
    },
    {
      name: 'PA Boot TE Drag',
      situation: 'Red Zone (inside 10)',
      successRate: 100,
      notes: '4/4 TDs — he bites on PA with Cover 1 Robber',
    },
    {
      name: 'HB Screen Left',
      situation: 'Edge blitz detected',
      successRate: 78,
      notes: 'Let the blitz come, screen to vacated side',
    },
    {
      name: 'Fade + Out Boundary',
      situation: 'Goal line Cover 1',
      successRate: 83,
      notes: 'Fade holds corner, out gets underneath robber',
    },
    {
      name: 'Jet Motion Quick Pass',
      situation: 'Aggressive press look',
      successRate: 75,
      notes: 'Motion forces late adjustment, quick slant money',
    },
  ],
  openingRecommendation: {
    play: 'Inside Zone — Establish the Run',
    confidence: 91,
    reason: 'xKillSwitch over-commits to pass rush early. Inside zone exploits vacated A-gaps and forces him to play honest. Sets up PA shots later.',
  },
  tendencies: [
    { label: 'DB Blitz on 3rd Long', frequency: '72%' },
    { label: 'Cover 1 Robber in Red Zone', frequency: '80%' },
    { label: 'Press Man on 1st Down', frequency: '65%' },
  ],
  tiltGuard: {
    readiness: 84,
    mood: 'focused',
    fatigue: 'fresh',
  },
  metaAlert: {
    weapon: 'Jet Motion + Quick Slant',
    notes: 'Beats his aggressive press alignment. Motion snap forces bail from press — slant is wide open.',
  },
  mentalReset: 'Breathe in 4 counts. Hold 4 counts. Out 4 counts. You have the data. You have the plan. One play at a time. Trust the process.',
  encounters: [
    {
      date: '2026-04-10',
      mode: 'Ranked H2H',
      result: 'W',
      score: '28-21',
      note: 'PA Boot was unstoppable in the red zone.',
    },
    {
      date: '2026-04-06',
      mode: 'Ranked H2H',
      result: 'L',
      score: '14-24',
      note: 'Got blitzed into oblivion early. Adjusted too late.',
    },
    {
      date: '2026-03-29',
      mode: 'MUT Champions',
      result: 'W',
      score: '35-17',
      note: 'Inside zone dominated all game. He never adjusted.',
    },
  ],
};

const MOCK_OPPONENT_BLITZ: OpponentData = {
  ...MOCK_OPPONENT,
  gamertag: 'BlitzMaster99',
  archetype: 'Pure Blitz Spammer',
  winRate: 75,
  winTrend: 'up',
  lastSeen: '5 days ago',
  dossierDepth: 11,
  tendencies: [
    { label: 'Send 5+ rushers', frequency: '78%' },
    { label: 'Cover 0 over the top', frequency: '46%' },
    { label: 'Press at the LOS', frequency: '71%' },
  ],
  metaAlert: {
    weapon: 'HB Screen + Quick Slants',
    notes: 'Quick releases neutralize his blitz before it hits the QB.',
  },
};

const MOCK_OPPONENT_AIRRAID: OpponentData = {
  ...MOCK_OPPONENT,
  gamertag: 'AirRaidKing',
  archetype: 'Spread Air Raid',
  winRate: 40,
  winTrend: 'down',
  lastSeen: '1 day ago',
  dossierDepth: 9,
  tendencies: [
    { label: 'Empty backfield 1st down', frequency: '62%' },
    { label: '4 verts vs 2-high', frequency: '54%' },
    { label: 'No-huddle tempo after big gains', frequency: '83%' },
  ],
  metaAlert: {
    weapon: 'Cover 4 Palms with robber',
    notes: 'Disguise palms — kills 4 verts and forces him underneath.',
  },
};

const MOCK_OPPONENTS_LIST: OpponentData[] = [
  MOCK_OPPONENT,
  MOCK_OPPONENT_BLITZ,
  MOCK_OPPONENT_AIRRAID,
];

// ---------- Counter Package Data ----------

const COUNTER_PACKAGE = {
  plays: [
    { name: 'Cover 3 Sky — Blitz Contain', desc: 'Sky safety force sets edge; 3-deep kills post routes.' },
    { name: 'Tampa 2 Shift', desc: 'MLB drops deep middle; takes away seam and TE drag.' },
    { name: 'Pinch Buck 0 — Fire Zone', desc: 'Interior pressure before quick passes develop.' },
    { name: 'Cover 6 Invert', desc: 'Rolls coverage to field; boundary flat defender jumps out routes.' },
  ],
  scheme: 'Nickel 3-3-5 Wide — focus on interior rush with spy on QB scrambles.',
  tip: 'Key adjustment: Shade outside on 1st down to take away his press-beater motion plays. Force him inside where your LBs can rally.',
};

// ---------- Sub-Components ----------

function OpponentHeader({
  data,
  onArchetypeClick,
}: {
  data: OpponentData;
  onArchetypeClick: () => void;
}) {
  return (
    <div className="rounded-xl border border-dark-700/50 bg-dark-900/80 p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-red-500/10">
            <Crosshair className="h-7 w-7 text-red-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-dark-50">{data.gamertag}</h2>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <button
                onClick={onArchetypeClick}
                className="rounded-full bg-red-500/15 px-2.5 py-0.5 text-[11px] font-medium text-red-400 transition-colors hover:bg-red-500/25 cursor-pointer"
              >
                {data.archetype}
              </button>
              <span className="text-xs text-dark-500">Last seen: {data.lastSeen}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-center">
            <div className="flex items-center gap-1">
              <span className="text-2xl font-bold text-dark-100">{data.winRate}%</span>
              {data.winTrend === 'up' ? (
                <TrendingUp className="h-4 w-4 text-forge-400" />
              ) : data.winTrend === 'down' ? (
                <TrendingDown className="h-4 w-4 text-red-400" />
              ) : null}
            </div>
            <span className="text-[11px] text-dark-500">Win Rate vs</span>
          </div>
          <div className="text-center">
            <div className="flex items-center gap-1">
              <Eye className="h-4 w-4 text-dark-400" />
              <span className="text-lg font-bold text-dark-100">{data.dossierDepth}</span>
            </div>
            <span className="text-[11px] text-dark-500">Intel Entries</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function KillSheet({ plays }: { plays: KillSheetPlay[] }) {
  return (
    <div className="rounded-xl border border-dark-700/50 bg-dark-900/80 p-5">
      <h3 className="mb-4 flex items-center gap-2 text-sm font-bold text-dark-100">
        <Crosshair className="h-4 w-4 text-red-400" />
        Kill Sheet — Top 5 Plays
      </h3>
      <div className="space-y-3">
        {plays.map((play, i) => (
          <div
            key={i}
            className="flex items-center gap-3 rounded-lg bg-dark-800/50 p-3"
          >
            <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-red-500/10 text-xs font-bold text-red-400">
              {i + 1}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-dark-100">{play.name}</p>
              <p className="text-[11px] text-dark-500">
                {play.situation} — {play.notes}
              </p>
            </div>
            <div
              className={clsx(
                'rounded-lg px-2 py-1 text-xs font-bold',
                play.successRate >= 85
                  ? 'bg-forge-500/15 text-forge-400'
                  : play.successRate >= 75
                  ? 'bg-blue-500/15 text-blue-400'
                  : 'bg-dark-700 text-dark-300'
              )}
            >
              {play.successRate}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function OpeningRecommendation({ rec }: { rec: OpponentData['openingRecommendation'] }) {
  return (
    <div className="rounded-xl border border-forge-500/30 bg-forge-500/5 p-5">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-bold text-dark-100">
        <Lightbulb className="h-4 w-4 text-forge-400" />
        Opening Recommendation
      </h3>
      <div className="flex items-start gap-4">
        <div className="min-w-0 flex-1">
          <p className="text-lg font-bold text-forge-400">{rec.play}</p>
          <p className="mt-2 text-sm leading-relaxed text-dark-300">{rec.reason}</p>
        </div>
        <div className="flex flex-col items-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-forge-500/15 text-sm font-bold text-forge-400">
            {rec.confidence}%
          </div>
          <span className="mt-1 text-[10px] text-dark-500">Confidence</span>
        </div>
      </div>
    </div>
  );
}

function TendenciesPills({ tendencies }: { tendencies: Tendency[] }) {
  return (
    <div className="rounded-xl border border-dark-700/50 bg-dark-900/80 p-5">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-bold text-dark-100">
        <Brain className="h-4 w-4 text-purple-400" />
        Top Tendencies
      </h3>
      <div className="flex flex-wrap gap-2">
        {tendencies.map((t, i) => (
          <div
            key={i}
            className="flex items-center gap-2 rounded-full bg-purple-500/10 px-3.5 py-2"
          >
            <span className="text-sm font-medium text-purple-300">{t.label}</span>
            <span className="rounded-full bg-purple-500/20 px-2 py-0.5 text-xs font-bold text-purple-400">
              {t.frequency}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

type Mood = TiltGuardStatus['mood'];

const MOOD_OPTIONS: { mood: Mood; label: string; emoji: string }[] = [
  { mood: 'focused', label: 'Locked In', emoji: '🔥' },
  { mood: 'confident', label: 'Good', emoji: '👍' },
  { mood: 'anxious', label: 'Anxious', emoji: '😬' },
  { mood: 'tilted', label: 'Tilted', emoji: '🌀' },
];

function TiltGuardStatusPanel({
  status,
  onUpdateMood,
}: {
  status: TiltGuardStatus;
  onUpdateMood: (mood: Mood) => void;
}) {
  const [picking, setPicking] = useState(false);

  const moodColors = {
    focused: 'text-forge-400 bg-forge-500/15',
    confident: 'text-blue-400 bg-blue-500/15',
    anxious: 'text-amber-400 bg-amber-500/15',
    tilted: 'text-red-400 bg-red-500/15',
  };

  const fatigueColors = {
    fresh: 'text-forge-400',
    moderate: 'text-amber-400',
    high: 'text-red-400',
  };

  const handlePick = (mood: Mood) => {
    onUpdateMood(mood);
    setPicking(false);
  };

  return (
    <div className="rounded-xl border border-dark-700/50 bg-dark-900/80 p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-bold text-dark-100">
          <Heart className="h-4 w-4 text-pink-400" />
          TiltGuard Status
        </h3>
        <button
          type="button"
          onClick={() => setPicking((p) => !p)}
          className="inline-flex items-center gap-1 rounded-md border border-dark-700 bg-dark-800/60 px-2 py-1 text-[11px] font-medium text-dark-300 transition-colors hover:bg-dark-700"
        >
          <Smile className="h-3 w-3" />
          Update Mood
        </button>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div className="text-center">
          <div className="text-2xl font-bold text-dark-100">{status.readiness}%</div>
          <span className="text-[11px] text-dark-500">Readiness</span>
        </div>
        <div className="flex flex-col items-center">
          <span className={clsx('rounded-full px-2.5 py-1 text-xs font-medium capitalize', moodColors[status.mood])}>
            {status.mood}
          </span>
          <span className="mt-1 text-[11px] text-dark-500">Mood</span>
        </div>
        <div className="flex flex-col items-center">
          <span className={clsx('text-sm font-bold capitalize', fatigueColors[status.fatigue])}>
            {status.fatigue}
          </span>
          <span className="mt-1 text-[11px] text-dark-500">Fatigue</span>
        </div>
      </div>
      {picking && (
        <div className="mt-3 rounded-lg border border-dark-700 bg-dark-800/60 p-3">
          <p className="mb-2 text-[11px] text-dark-400">How are you feeling right now?</p>
          <div className="flex flex-wrap gap-1.5">
            {MOOD_OPTIONS.map((opt) => (
              <button
                key={opt.mood}
                type="button"
                onClick={() => handlePick(opt.mood)}
                className={clsx(
                  'inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors',
                  status.mood === opt.mood
                    ? 'border-forge-500/40 bg-forge-500/15 text-forge-300'
                    : 'border-dark-700 bg-dark-800 text-dark-300 hover:border-dark-500 hover:bg-dark-700'
                )}
              >
                <span aria-hidden="true">{opt.emoji}</span>
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      )}
      {status.readiness < 70 && (
        <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-2 text-[11px] text-amber-200">
          Your readiness is low — consider running the Mental Reset before
          entering the game.
        </div>
      )}
    </div>
  );
}

function MetaAlertPanel({ meta }: { meta: OpponentData['metaAlert'] }) {
  return (
    <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-5">
      <h3 className="mb-2 flex items-center gap-2 text-sm font-bold text-dark-100">
        <AlertTriangle className="h-4 w-4 text-amber-400" />
        Meta Alert
      </h3>
      <p className="text-base font-bold text-amber-400">{meta.weapon}</p>
      <p className="mt-1 text-sm text-dark-400">{meta.notes}</p>
    </div>
  );
}

// ---------- 2A: Mental Reset Panel (Full 5-step protocol) ----------

function MentalResetPanel() {
  const [activated, setActivated] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [breathTimer, setBreathTimer] = useState(30);
  const [breathPhase, setBreathPhase] = useState<'inhale' | 'hold1' | 'exhale' | 'hold2'>('inhale');
  const [breathPhaseTime, setBreathPhaseTime] = useState(4);
  const [resetComplete, setResetComplete] = useState(false);

  // Breath timer countdown
  useEffect(() => {
    if (!activated || currentStep !== 1 || breathTimer <= 0) return;
    const interval = setInterval(() => {
      setBreathTimer((t) => {
        if (t <= 1) {
          setCurrentStep(2);
          return 0;
        }
        return t - 1;
      });
      setBreathPhaseTime((pt) => {
        if (pt <= 1) {
          setBreathPhase((p) => {
            if (p === 'inhale') return 'hold1';
            if (p === 'hold1') return 'exhale';
            if (p === 'exhale') return 'hold2';
            return 'inhale';
          });
          return 4;
        }
        return pt - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [activated, currentStep, breathTimer]);

  // Reset complete confirmation timer
  useEffect(() => {
    if (!resetComplete) return;
    const timeout = setTimeout(() => {
      setResetComplete(false);
    }, 3000);
    return () => clearTimeout(timeout);
  }, [resetComplete]);

  const handleComplete = () => {
    setActivated(false);
    setCurrentStep(1);
    setBreathTimer(30);
    setBreathPhase('inhale');
    setBreathPhaseTime(4);
    setResetComplete(true);
  };

  const handleClose = () => {
    setActivated(false);
    setCurrentStep(1);
    setBreathTimer(30);
    setBreathPhase('inhale');
    setBreathPhaseTime(4);
  };

  const phaseLabel = {
    inhale: 'Inhale',
    hold1: 'Hold',
    exhale: 'Exhale',
    hold2: 'Hold',
  };

  if (resetComplete) {
    return (
      <div className="rounded-xl border border-forge-500/30 bg-forge-500/5 p-5">
        <p className="text-center text-sm font-medium text-forge-400">
          Mental reset complete ✓
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-dark-700/50 bg-dark-900/80 p-5">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-bold text-dark-100">
        <RotateCcw className="h-4 w-4 text-teal-400" />
        Mental Reset
      </h3>
      {activated ? (
        <div className="relative space-y-4">
          <button
            onClick={handleClose}
            className="absolute right-0 top-0 text-dark-500 hover:text-dark-300"
          >
            <X className="h-4 w-4" />
          </button>

          {/* Step indicator */}
          <div className="flex items-center gap-2 text-xs text-dark-500">
            {[1, 2, 3, 4].map((s) => (
              <div
                key={s}
                className={clsx(
                  'flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold',
                  s === currentStep
                    ? 'bg-teal-500/20 text-teal-400'
                    : s < currentStep
                    ? 'bg-forge-500/20 text-forge-400'
                    : 'bg-dark-800 text-dark-600'
                )}
              >
                {s}
              </div>
            ))}
          </div>

          {/* Step 1: BREATHE */}
          {currentStep === 1 && (
            <div className="rounded-lg bg-teal-500/5 p-4 space-y-3">
              <p className="text-sm font-bold text-teal-400">Step 1: BREATHE</p>
              <p className="text-lg font-bold text-teal-300">
                {phaseLabel[breathPhase]} — {breathPhaseTime}
              </p>
              <p className="text-xs text-dark-400">
                Box breathing: Inhale 4 → Hold 4 → Exhale 4 → Hold 4
              </p>
              {/* Progress bar */}
              <div className="h-2 w-full rounded-full bg-dark-800">
                <div
                  className="h-2 rounded-full bg-teal-500 transition-all duration-1000"
                  style={{ width: `${((30 - breathTimer) / 30) * 100}%` }}
                />
              </div>
              <p className="text-xs text-dark-500 text-right">{breathTimer}s remaining</p>
              <button
                onClick={() => setCurrentStep(2)}
                className="text-xs text-dark-500 hover:text-dark-300"
              >
                Skip →
              </button>
            </div>
          )}

          {/* Step 2: RELEASE THE LAST GAME */}
          {currentStep === 2 && (
            <div className="rounded-lg bg-teal-500/5 p-4 space-y-3">
              <p className="text-sm font-bold text-teal-400">Step 2: RELEASE THE LAST GAME</p>
              <p className="text-sm leading-relaxed text-teal-300 italic">
                &quot;That game is done. The score is final. It cannot affect this game unless you carry it.&quot;
              </p>
              <button
                onClick={() => setCurrentStep(3)}
                className="rounded-lg bg-teal-500/10 px-3 py-2 text-xs font-medium text-teal-400 hover:bg-teal-500/20"
              >
                Next →
              </button>
            </div>
          )}

          {/* Step 3: THREE FOCUS POINTS */}
          {currentStep === 3 && (
            <div className="rounded-lg bg-teal-500/5 p-4 space-y-3">
              <p className="text-sm font-bold text-teal-400">Step 3: THREE FOCUS POINTS</p>
              <ul className="space-y-2">
                <li className="flex items-center gap-2 text-sm text-teal-300">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-teal-500/20 text-[10px] font-bold text-teal-400">1</span>
                  Pre-snap coverage ID
                </li>
                <li className="flex items-center gap-2 text-sm text-teal-300">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-teal-500/20 text-[10px] font-bold text-teal-400">2</span>
                  One read at a time
                </li>
                <li className="flex items-center gap-2 text-sm text-teal-300">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-teal-500/20 text-[10px] font-bold text-teal-400">3</span>
                  Trust your scheme
                </li>
              </ul>
              <button
                onClick={() => setCurrentStep(4)}
                className="rounded-lg bg-teal-500/10 px-3 py-2 text-xs font-medium text-teal-400 hover:bg-teal-500/20"
              >
                Next →
              </button>
            </div>
          )}

          {/* Step 4: DECLARE READY */}
          {currentStep === 4 && (
            <div className="rounded-lg bg-teal-500/5 p-4 space-y-3">
              <p className="text-sm font-bold text-teal-400">Step 4: DECLARE READY</p>
              <p className="text-sm leading-relaxed text-teal-300 italic">
                &quot;Say aloud: I am locked in. Let&apos;s go.&quot;
              </p>
            </div>
          )}

          {/* Complete button */}
          <button
            onClick={handleComplete}
            className="w-full rounded-lg bg-forge-500/15 px-4 py-3 text-sm font-bold text-forge-400 transition-colors hover:bg-forge-500/25"
          >
            Reset Complete — I&apos;m Ready
          </button>
        </div>
      ) : (
        <button
          onClick={() => setActivated(true)}
          className="w-full rounded-lg bg-teal-500/10 px-4 py-3 text-sm font-medium text-teal-400 transition-colors hover:bg-teal-500/20"
        >
          Tap to Reset
        </button>
      )}
    </div>
  );
}

// ---------- 2F: Last Encounters Card ----------

function LastEncountersCard({ encounters }: { encounters: Encounter[] }) {
  return (
    <div className="rounded-xl border border-dark-700/50 bg-dark-900/80 p-5">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-bold text-dark-100">
        <Clock className="h-4 w-4 text-blue-400" />
        Last 3 Encounters
      </h3>
      <div className="space-y-3">
        {encounters.map((enc, i) => (
          <div key={i} className="rounded-lg bg-dark-800/50 p-3 space-y-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className={clsx(
                    'rounded px-1.5 py-0.5 text-xs font-bold',
                    enc.result === 'W'
                      ? 'bg-green-500/15 text-green-400'
                      : 'bg-red-500/15 text-red-400'
                  )}
                >
                  {enc.result}
                </span>
                <span className="text-sm font-medium text-dark-100">{enc.score}</span>
              </div>
              <span className="text-[11px] text-dark-500">{enc.date}</span>
            </div>
            <p className="text-[11px] text-dark-500">{enc.mode}</p>
            <p className="text-xs italic text-dark-400">&quot;{enc.note}&quot;</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------- 2C: Archetype Counter Panel ----------

function ArchetypeCounterPanel({ onClose }: { onClose: () => void }) {
  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/60"
        onClick={onClose}
      />
      {/* Slide-over panel */}
      <div className="fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col bg-dark-900 border-l border-dark-700/50 shadow-2xl">
        <div className="flex items-center justify-between border-b border-dark-700/50 p-5">
          <h3 className="text-sm font-bold text-dark-100 flex items-center gap-2">
            <Shield className="h-4 w-4 text-red-400" />
            Counter Package: Blitz Heavy Aggressor
          </h3>
          <button onClick={onClose} className="text-dark-500 hover:text-dark-300">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Counter plays */}
          <div>
            <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-dark-500">Counter Plays</h4>
            <div className="space-y-2">
              {COUNTER_PACKAGE.plays.map((play, i) => (
                <div key={i} className="rounded-lg bg-dark-800/50 p-3">
                  <p className="text-sm font-medium text-dark-100">{play.name}</p>
                  <p className="text-[11px] text-dark-400 mt-1">{play.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Defensive scheme */}
          <div>
            <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-dark-500">Defensive Scheme</h4>
            <p className="text-sm text-dark-300 rounded-lg bg-dark-800/50 p-3">{COUNTER_PACKAGE.scheme}</p>
          </div>

          {/* Key adjustment */}
          <div>
            <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-dark-500">Key Adjustment</h4>
            <p className="text-sm text-amber-300 rounded-lg bg-amber-500/5 border border-amber-500/20 p-3">{COUNTER_PACKAGE.tip}</p>
          </div>

          {/* Add all button */}
          <button
            onClick={() => {
              console.log('[WarRoom] Adding counter package to gameplan');
              onClose();
            }}
            className="w-full rounded-lg bg-forge-500/15 px-4 py-3 text-sm font-bold text-forge-400 transition-colors hover:bg-forge-500/25"
          >
            Add All to Gameplan
          </button>
        </div>
      </div>
    </>
  );
}

function CountdownTimer() {
  const [totalSeconds, setTotalSeconds] = useState(300); // 5 min default
  const [remaining, setRemaining] = useState(300);
  const [isRunning, setIsRunning] = useState(false);
  const [customMinutes, setCustomMinutes] = useState('');
  const [showHydration, setShowHydration] = useState(false);
  const completedRef = useState({ fired: false })[0];

  useEffect(() => {
    if (!isRunning || remaining <= 0) return;
    const interval = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          setIsRunning(false);
          return 0;
        }
        return r - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [isRunning, remaining]);

  // Fire the hydration overlay + VoiceForge speak exactly once when the timer
  // hits zero from a running state. The completed ref keeps us idempotent.
  useEffect(() => {
    if (remaining === 0 && !completedRef.fired && totalSeconds > 0) {
      completedRef.fired = true;
      setShowHydration(true);
      try {
        VoiceForgeService.speak(
          'Briefing complete. Drink water. Stand up. Take a breath. You are ready.',
          { interruptCurrent: true, priority: 'high' }
        );
      } catch {
        /* noop — VoiceForge offline */
      }
      const t = window.setTimeout(() => setShowHydration(false), 8000);
      return () => window.clearTimeout(t);
    }
    return undefined;
  }, [remaining, totalSeconds, completedRef]);

  const minutes = Math.floor(remaining / 60);
  const seconds = remaining % 60;

  const presets = [60, 180, 300, 600, 900, 1800, 3600];

  const setPreset = (secs: number) => {
    setTotalSeconds(secs);
    setRemaining(secs);
    setIsRunning(false);
    completedRef.fired = false;
  };

  const applyCustom = () => {
    const mins = Number(customMinutes);
    if (!Number.isFinite(mins) || mins <= 0 || mins > 180) return;
    setPreset(Math.round(mins * 60));
    setCustomMinutes('');
  };

  return (
    <div className="rounded-xl border border-dark-700/50 bg-dark-900/80 p-5">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-bold text-dark-100">
        <Timer className="h-4 w-4 text-blue-400" />
        Countdown Timer
      </h3>

      <div className="text-center">
        <div className={clsx(
          'text-4xl font-mono font-bold',
          remaining === 0 ? 'text-red-400' : remaining <= 30 ? 'text-amber-400' : 'text-dark-100'
        )}>
          {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
        </div>

        <div className="mt-3 flex items-center justify-center gap-2">
          <button
            onClick={() => {
              if (remaining === 0) {
                setRemaining(totalSeconds);
                completedRef.fired = false;
              }
              setIsRunning(!isRunning);
            }}
            className="flex items-center gap-1.5 rounded-lg bg-forge-500/15 px-4 py-2 text-sm font-medium text-forge-400 transition-colors hover:bg-forge-500/25"
          >
            {isRunning ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
            {isRunning ? 'Pause' : 'Start'}
          </button>
          <button
            onClick={() => {
              setRemaining(totalSeconds);
              setIsRunning(false);
              completedRef.fired = false;
            }}
            className="rounded-lg bg-dark-800 px-3 py-2 text-sm text-dark-400 transition-colors hover:text-dark-200"
          >
            Reset
          </button>
        </div>

        <div className="mt-3 flex flex-wrap justify-center gap-2">
          {presets.map((p) => (
            <button
              key={p}
              onClick={() => setPreset(p)}
              className={clsx(
                'rounded-full px-2.5 py-1 text-xs font-medium transition-colors',
                totalSeconds === p
                  ? 'bg-forge-500/20 text-forge-400'
                  : 'bg-dark-800 text-dark-500 hover:text-dark-300'
              )}
            >
              {p >= 60 ? `${p / 60}m` : `${p}s`}
            </button>
          ))}
        </div>

        <div className="mt-3 flex items-center justify-center gap-1.5">
          <input
            type="number"
            inputMode="numeric"
            min={1}
            max={180}
            value={customMinutes}
            onChange={(e) => setCustomMinutes(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') applyCustom();
            }}
            placeholder="Custom"
            className="w-20 rounded-md border border-dark-700 bg-dark-800 px-2 py-1 text-center text-xs text-dark-200 placeholder-dark-500 focus:border-forge-500 focus:outline-none"
          />
          <span className="text-[11px] text-dark-500">min</span>
          <button
            type="button"
            onClick={applyCustom}
            disabled={!customMinutes.trim()}
            className="rounded-md border border-dark-700 bg-dark-800 px-2 py-1 text-[11px] font-medium text-dark-300 transition-colors hover:bg-dark-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Set
          </button>
        </div>
      </div>

      {showHydration && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
          <div className="max-w-sm rounded-xl border border-forge-500/40 bg-dark-900 p-6 text-center shadow-xl">
            <Droplets className="mx-auto mb-3 h-10 w-10 text-blue-400" />
            <h3 className="text-lg font-bold text-dark-50">Time&apos;s Up</h3>
            <p className="mt-2 text-sm text-dark-300">
              Drink water. Stand up. Take a breath. You&apos;re ready.
            </p>
            <button
              type="button"
              onClick={() => setShowHydration(false)}
              className="mt-4 rounded-lg bg-forge-500/15 px-4 py-2 text-xs font-semibold text-forge-300 transition-colors hover:bg-forge-500/25"
            >
              I&apos;m ready
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------- Main Component ----------

export default function PreGameWarRoom() {
  const router = useRouter();
  const startSession = useSessionStore((s) => s.startSession);
  const [showArchetypePanel, setShowArchetypePanel] = useState(false);
  const [quickNote, setQuickNote] = useState('');
  const [noteSaved, setNoteSaved] = useState(false);
  const [selectedGamertag, setSelectedGamertag] = useState<string>(
    MOCK_OPPONENTS_LIST[0]?.gamertag ?? 'xKillSwitch'
  );
  const [tiltGuard, setTiltGuard] = useState<TiltGuardStatus>(
    MOCK_OPPONENTS_LIST[0]?.tiltGuard ?? MOCK_OPPONENT.tiltGuard
  );
  const [refreshKey, setRefreshKey] = useState(0);
  const [entering, setEntering] = useState(false);

  // 2B: VoiceForge
  const { speak, stop, isSpeaking, isAvailable } = useVoiceForge();

  const data: OpponentData = {
    ...(MOCK_OPPONENTS_LIST.find((o) => o.gamertag === selectedGamertag) ??
      MOCK_OPPONENT),
    tiltGuard,
  };

  // Reset mood + readiness when the active opponent changes so the panel
  // reflects the new context (each opponent's TiltGuard mock is the starting
  // point; mood updates layer on top).
  useEffect(() => {
    const next = MOCK_OPPONENTS_LIST.find((o) => o.gamertag === selectedGamertag);
    if (next) setTiltGuard(next.tiltGuard);
  }, [selectedGamertag]);

  // Recompute readiness when mood changes — focused/confident keep readiness
  // high, anxious/tilted drop it. This mirrors what the backend TiltGuard
  // service would do and lets the low-readiness warning fire on mood swings.
  const handleUpdateMood = useCallback((mood: Mood) => {
    setTiltGuard((prev) => {
      const moodReadiness: Record<Mood, number> = {
        focused: 92,
        confident: 86,
        anxious: 64,
        tilted: 48,
      };
      return { ...prev, mood, readiness: moodReadiness[mood] };
    });
  }, []);

  const handleRefreshBrief = useCallback(() => {
    setRefreshKey((k) => k + 1);
    setNoteSaved(false);
  }, []);

  const handleEnterGame = useCallback(() => {
    setEntering(true);
    try {
      startSession('ranked', { opponent: data.gamertag });
    } catch {
      /* sessionStore unavailable in test envs — non-fatal */
    }
    try {
      VoiceForgeService.speak(
        `Briefing complete. ${data.gamertag} runs ${data.tendencies[0]?.label ?? 'a varied scheme'} ${data.tendencies[0]?.frequency ?? ''}. Your kill shot is ${data.killSheet[0]?.name ?? 'your top play'}. You are ready.`,
        { interruptCurrent: true, priority: 'high' }
      );
    } catch {
      /* VoiceForge offline */
    }
    router.push('/dashboard');
  }, [data, router, startSession]);

  // 2B: Compile and speak briefing
  const handleReadBriefing = useCallback(() => {
    if (isSpeaking) {
      stop();
      return;
    }
    const briefingText = [
      `Opponent: ${data.gamertag}, archetype ${data.archetype}.`,
      `Kill sheet top plays: ${data.killSheet.map((p) => p.name).join(', ')}.`,
      `Key tendencies: ${data.tendencies.map((t) => `${t.label} at ${t.frequency}`).join(', ')}.`,
      `Opening recommendation: ${data.openingRecommendation.play} with ${data.openingRecommendation.confidence}% confidence. ${data.openingRecommendation.reason}`,
      `TiltGuard status: readiness ${data.tiltGuard.readiness}%, mood ${data.tiltGuard.mood}, fatigue ${data.tiltGuard.fatigue}.`,
    ].join(' ');
    speak(briefingText);
  }, [isSpeaking, stop, speak, data]);

  // 2E: Save quick note
  const handleSaveNote = useCallback(() => {
    if (!quickNote.trim()) return;
    console.log('[WarRoom] POST /api/vault/notes', { note: quickNote });
    setQuickNote('');
    setNoteSaved(true);
    setTimeout(() => setNoteSaved(false), 2000);
  }, [quickNote]);

  return (
    <div className="space-y-5">
      {/* Opponent selector + Refresh + Read Briefing */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-dark-500">
            vs
          </span>
          <div className="relative">
            <select
              value={selectedGamertag}
              onChange={(e) => setSelectedGamertag(e.target.value)}
              className="appearance-none rounded-lg border border-dark-700 bg-dark-900/80 px-3 pr-8 py-2 text-sm font-semibold text-dark-100 transition-colors hover:border-dark-500 focus:border-forge-500 focus:outline-none"
            >
              {MOCK_OPPONENTS_LIST.map((o) => (
                <option key={o.gamertag} value={o.gamertag}>
                  {o.gamertag}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-400" />
          </div>
          <button
            type="button"
            onClick={handleRefreshBrief}
            className="inline-flex items-center gap-1.5 rounded-lg border border-dark-700 bg-dark-900/80 px-3 py-2 text-xs font-medium text-dark-300 transition-colors hover:border-dark-500 hover:bg-dark-800"
            title="Regenerate the briefing with current data"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Refresh Brief
          </button>
        </div>
        {isAvailable && (
          <button
            onClick={handleReadBriefing}
            className={clsx(
              'flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors',
              isSpeaking
                ? 'bg-amber-500/15 text-amber-400 hover:bg-amber-500/25'
                : 'bg-forge-500/15 text-forge-400 hover:bg-forge-500/25'
            )}
          >
            <Volume2 className="h-4 w-4" />
            {isSpeaking ? 'Reading...' : 'Read Briefing'}
          </button>
        )}
      </div>

      {/* Opponent Header */}
      <OpponentHeader
        key={`${selectedGamertag}-${refreshKey}`}
        data={data}
        onArchetypeClick={() => setShowArchetypePanel(true)}
      />

      {/* 2C: Archetype Counter Panel slide-over */}
      {showArchetypePanel && (
        <ArchetypeCounterPanel onClose={() => setShowArchetypePanel(false)} />
      )}

      {/* Two column layout */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Left column */}
        <div className="space-y-5">
          <KillSheet plays={data.killSheet} />
          {/* 2D: View Full Gameplan link */}
          <div className="flex justify-end -mt-3">
            <Link href="/gameplan" className="text-xs text-dark-500 hover:text-dark-300 transition-colors">
              View Full Gameplan →
            </Link>
          </div>
          <TendenciesPills tendencies={data.tendencies} />
          {/* 2D: View Full Dossier link */}
          <div className="flex justify-end -mt-3">
            <Link href="/opponents/xKillSwitch" className="text-xs text-dark-500 hover:text-dark-300 transition-colors">
              View Full Dossier →
            </Link>
          </div>
          {/* 2F: Last 3 Encounters */}
          <LastEncountersCard encounters={data.encounters} />
          <MentalResetPanel />
        </div>

        {/* Right column */}
        <div className="space-y-5">
          <OpeningRecommendation rec={data.openingRecommendation} />
          <TiltGuardStatusPanel
            status={tiltGuard}
            onUpdateMood={handleUpdateMood}
          />
          <MetaAlertPanel meta={data.metaAlert} />
          <CountdownTimer />
        </div>
      </div>

      {/* 2E: Quick Notes */}
      <div className="rounded-xl border border-dark-700/50 bg-dark-900/80 p-5">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-bold text-dark-100">
          <FileText className="h-4 w-4 text-dark-400" />
          Quick Note
        </h3>
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={quickNote}
            onChange={(e) => setQuickNote(e.target.value.slice(0, 200))}
            maxLength={200}
            placeholder="Jot a quick note before the game..."
            className="flex-1 rounded-lg bg-dark-800/50 border border-dark-700/50 px-3 py-2 text-sm text-dark-100 placeholder-dark-600 outline-none focus:border-forge-500/50"
          />
          <button
            onClick={handleSaveNote}
            disabled={!quickNote.trim()}
            className={clsx(
              'rounded-lg px-4 py-2 text-sm font-medium transition-colors',
              quickNote.trim()
                ? 'bg-forge-500/15 text-forge-400 hover:bg-forge-500/25'
                : 'bg-dark-800 text-dark-600 cursor-not-allowed'
            )}
          >
            Save
          </button>
        </div>
        {noteSaved && (
          <p className="mt-2 text-xs text-forge-400">Note saved to ForgeVault ✓</p>
        )}
      </div>

      {/* Enter the game — starts the ranked session and routes to the
          dashboard so CompetitionModeCard takes over. */}
      <button
        onClick={handleEnterGame}
        disabled={entering}
        className="group flex w-full items-center justify-center gap-3 rounded-xl border border-forge-500/30 bg-forge-500/10 py-4 text-lg font-bold text-forge-400 transition-all hover:bg-forge-500/20 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <Zap className="h-5 w-5" />
        Ready. Enter the game.
        <ChevronRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
      </button>
    </div>
  );
}

/**
 * PreGameWarRoom — Full pre-game briefing component.
 * Opponent header, kill sheet, opening recommendation, tendencies,
 * TiltGuard status, meta alert, mental reset, timer, and exit.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
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
  Flame,
  Eye,
} from 'lucide-react';
import { clsx } from 'clsx';

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
}

// ---------- Mock Data ----------

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
};

// ---------- Sub-Components ----------

function OpponentHeader({ data }: { data: OpponentData }) {
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
              <span className="rounded-full bg-red-500/15 px-2.5 py-0.5 text-[11px] font-medium text-red-400">
                {data.archetype}
              </span>
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

function TiltGuardStatusPanel({ status }: { status: TiltGuardStatus }) {
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

  return (
    <div className="rounded-xl border border-dark-700/50 bg-dark-900/80 p-5">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-bold text-dark-100">
        <Heart className="h-4 w-4 text-pink-400" />
        TiltGuard Status
      </h3>
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

function MentalResetPanel({ script }: { script: string }) {
  const [activated, setActivated] = useState(false);

  return (
    <div className="rounded-xl border border-dark-700/50 bg-dark-900/80 p-5">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-bold text-dark-100">
        <RotateCcw className="h-4 w-4 text-teal-400" />
        Mental Reset
      </h3>
      {activated ? (
        <div className="rounded-lg bg-teal-500/5 p-4">
          <p className="text-sm leading-relaxed text-teal-300">{script}</p>
          <button
            onClick={() => setActivated(false)}
            className="mt-3 text-xs text-dark-500 hover:text-dark-300"
          >
            Dismiss
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

function CountdownTimer() {
  const [totalSeconds, setTotalSeconds] = useState(300); // 5 min default
  const [remaining, setRemaining] = useState(300);
  const [isRunning, setIsRunning] = useState(false);

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

  const minutes = Math.floor(remaining / 60);
  const seconds = remaining % 60;

  const presets = [60, 180, 300, 600];

  const setPreset = (secs: number) => {
    setTotalSeconds(secs);
    setRemaining(secs);
    setIsRunning(false);
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
              if (remaining === 0) setRemaining(totalSeconds);
              setIsRunning(!isRunning);
            }}
            className="flex items-center gap-1.5 rounded-lg bg-forge-500/15 px-4 py-2 text-sm font-medium text-forge-400 transition-colors hover:bg-forge-500/25"
          >
            {isRunning ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
            {isRunning ? 'Pause' : 'Start'}
          </button>
          <button
            onClick={() => { setRemaining(totalSeconds); setIsRunning(false); }}
            className="rounded-lg bg-dark-800 px-3 py-2 text-sm text-dark-400 transition-colors hover:text-dark-200"
          >
            Reset
          </button>
        </div>

        <div className="mt-3 flex justify-center gap-2">
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
      </div>
    </div>
  );
}

// ---------- Main Component ----------

export default function PreGameWarRoom() {
  const [exited, setExited] = useState(false);
  const data = MOCK_OPPONENT;

  if (exited) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <div className="rounded-xl border border-forge-500/30 bg-forge-500/5 p-10 text-center">
          <Flame className="mx-auto mb-4 h-12 w-12 text-forge-400" />
          <h2 className="text-2xl font-bold text-dark-50">Ready. Enter the game.</h2>
          <p className="mt-2 text-dark-400">You have the intel. Trust your preparation.</p>
          <button
            onClick={() => setExited(false)}
            className="mt-6 rounded-lg bg-dark-800 px-4 py-2 text-sm text-dark-400 hover:text-dark-200"
          >
            Back to War Room
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Opponent Header */}
      <OpponentHeader data={data} />

      {/* Two column layout */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Left column */}
        <div className="space-y-5">
          <KillSheet plays={data.killSheet} />
          <TendenciesPills tendencies={data.tendencies} />
          <MentalResetPanel script={data.mentalReset} />
        </div>

        {/* Right column */}
        <div className="space-y-5">
          <OpeningRecommendation rec={data.openingRecommendation} />
          <TiltGuardStatusPanel status={data.tiltGuard} />
          <MetaAlertPanel meta={data.metaAlert} />
          <CountdownTimer />
        </div>
      </div>

      {/* Exit Button */}
      <button
        onClick={() => setExited(true)}
        className="group flex w-full items-center justify-center gap-3 rounded-xl border border-forge-500/30 bg-forge-500/10 py-4 text-lg font-bold text-forge-400 transition-all hover:bg-forge-500/20"
      >
        <Zap className="h-5 w-5" />
        Ready. Enter the game.
        <ChevronRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
      </button>
    </div>
  );
}

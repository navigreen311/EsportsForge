/**
 * Daily Forge Card — Daily mission card with drill, focus, mental cue,
 * meta tip, server-side completion + streak persistence.
 *
 * Toggling a check optimistically updates local state and PATCHes the
 * backend (`/api/v1/daily-forge/today`). On error we revert the local
 * state. When all 4 flags become true we render the completion banner +
 * a transient streak toast.
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  Flame,
  Target,
  Brain,
  Lightbulb,
  Zap,
  RefreshCw,
  CheckCircle2,
  Circle,
  Loader2,
} from 'lucide-react';
import { clsx } from 'clsx';
import api from '@/lib/api';
import { useSessionStore } from '@/lib/sessionStore';
import { useMyArsenal } from '@/hooks/useArsenal';

interface DailyMission {
  drill: { title: string; irScore: number; time: string };
  focus: string;
  mentalCue: string;
  metaTip: string;
}

const MOCK_MISSIONS: DailyMission[] = [
  {
    drill: { title: 'Cover 3 Beater — Flood Right', irScore: 87, time: '12 min' },
    focus: 'Attack the flat defender with RB wheel route when Cover 3 is detected',
    mentalCue: 'Breathe before the snap. Trust your first read — hesitation kills drives.',
    metaTip: 'Meta alert: Gun Bunch is seeing 34% more Cover 4 this week. Adjust your audibles.',
  },
  {
    drill: { title: 'Red Zone Efficiency — Goal Line', irScore: 92, time: '8 min' },
    focus: 'Use play-action near the goal line to exploit aggressive LB play',
    mentalCue: 'Stay present. One play at a time. The scoreboard takes care of itself.',
    metaTip: 'Shotgun formations in the red zone have a 12% higher TD rate this patch.',
  },
  {
    drill: { title: 'Pocket Awareness — Slide Protection', irScore: 79, time: '15 min' },
    focus: 'Identify the blitzer pre-snap and hot route the RB to the vacated zone',
    mentalCue: 'If tilted, take a 30-second pause. Composure is your competitive edge.',
    metaTip: 'Nickel blitz packages are up 22% in ranked — expect extra pressure from slot.',
  },
];

type DailyForgeKey = 'drill' | 'focus' | 'mental' | 'meta';

const KEYS: DailyForgeKey[] = ['drill', 'focus', 'mental', 'meta'];

interface ServerStatus {
  drill_done: boolean;
  focus_done: boolean;
  mental_done: boolean;
  meta_done: boolean;
  all_complete: boolean;
  current_streak: number;
}

const STORAGE_KEY = 'dailyforge_local_meta';

interface LocalMeta {
  date: string;
  drillInProgress: boolean;
  missionIndex: number;
  history: string[];
}

function getTodayStr(): string {
  return new Date().toISOString().split('T')[0]!;
}

function defaultMeta(): LocalMeta {
  return {
    date: getTodayStr(),
    drillInProgress: false,
    missionIndex: Math.floor(Math.random() * MOCK_MISSIONS.length),
    history: [],
  };
}

function loadMeta(): LocalMeta {
  if (typeof window === 'undefined') return defaultMeta();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultMeta();
    const parsed: LocalMeta = JSON.parse(raw);
    // Roll over to today if the date has changed.
    if (parsed.date !== getTodayStr()) {
      return {
        date: getTodayStr(),
        drillInProgress: false,
        missionIndex: Math.floor(Math.random() * MOCK_MISSIONS.length),
        history: parsed.history ?? [],
      };
    }
    return { ...defaultMeta(), ...parsed };
  } catch {
    return defaultMeta();
  }
}

function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

const DEFAULT_STATUS: ServerStatus = {
  drill_done: false,
  focus_done: false,
  mental_done: false,
  meta_done: false,
  all_complete: false,
  current_streak: 0,
};

export function DailyForgeCard() {
  const [status, setStatus] = useState<ServerStatus>(DEFAULT_STATUS);
  const [meta, setMeta] = useState<LocalMeta>(defaultMeta);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const router = useRouter();
  const startSession = useSessionStore((s) => s.startSession);
  const { data: savedWeapons = [] } = useMyArsenal();
  const featuredWeapon = savedWeapons[0];
  const wasAllCompleteRef = useRef(false);

  // Hydrate local-only meta (drill-in-progress, mission rotation) from localStorage.
  useEffect(() => {
    setMeta(loadMeta());
  }, []);

  // Persist local-only meta.
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(meta));
    }
  }, [meta]);

  // Fetch server state on mount.
  useEffect(() => {
    let cancelled = false;
    api
      .get<ServerStatus>('/daily-forge/today')
      .then((res) => {
        if (cancelled) return;
        setStatus(res.data);
        wasAllCompleteRef.current = res.data.all_complete;
      })
      .catch(() => {
        // Auth or network error — leave defaults.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const mission = MOCK_MISSIONS[meta.missionIndex % MOCK_MISSIONS.length]!;
  const allComplete = status.all_complete;

  const checks: boolean[] = [
    status.drill_done,
    status.focus_done,
    status.mental_done,
    status.meta_done,
  ];

  const patchKey = useCallback(
    async (key: DailyForgeKey, done: boolean) => {
      const previous = status;
      // Optimistic update
      const optimistic: ServerStatus = {
        ...status,
        [`${key}_done`]: done,
      } as ServerStatus;
      optimistic.all_complete =
        optimistic.drill_done &&
        optimistic.focus_done &&
        optimistic.mental_done &&
        optimistic.meta_done;
      setStatus(optimistic);
      try {
        const res = await api.patch<ServerStatus>('/daily-forge/today', {
          key,
          done,
        });
        setStatus(res.data);
        // Fire celebration toast on the all-complete edge.
        if (res.data.all_complete && !wasAllCompleteRef.current) {
          setToastMessage(
            `Day ${res.data.current_streak} complete — keep the streak alive`,
          );
          window.setTimeout(() => setToastMessage(null), 3500);
        }
        wasAllCompleteRef.current = res.data.all_complete;
      } catch {
        // Revert on failure.
        setStatus(previous);
      }
    },
    [status],
  );

  const toggleCheck = useCallback(
    (idx: number) => {
      const key = KEYS[idx];
      if (!key) return;
      const next = !checks[idx];
      // Drill click also clears the in-progress amber state.
      if (idx === 0 && next) {
        setMeta((prev) => ({ ...prev, drillInProgress: false }));
      }
      void patchKey(key, next);
    },
    [checks, patchKey],
  );

  const handleDrillClick = useCallback(() => {
    if (checks[0]) return; // already complete
    setMeta((prev) => ({ ...prev, drillInProgress: true }));
    startSession('training', { drillId: mission.drill.title });
    const drillSlug = slugify(mission.drill.title);
    // Toggle drill complete + navigate alongside.
    void patchKey('drill', true);
    router.push(`/drills?dailyForgeDrill=${encodeURIComponent(drillSlug)}`);
  }, [checks, mission.drill.title, startSession, router, patchKey]);

  const regenerate = useCallback(() => {
    setMeta((prev) => ({
      ...prev,
      missionIndex: (prev.missionIndex + 1) % MOCK_MISSIONS.length,
      drillInProgress: false,
    }));
  }, []);

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
  });

  // Build 14-day calendar dots from local history + today's all-complete flag.
  const calendarDots = Array.from({ length: 14 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (13 - i));
    const dateStr = d.toISOString().split('T')[0]!;
    const isToday = dateStr === getTodayStr();
    const completed = meta.history.includes(dateStr) || (isToday && allComplete);
    return { dateStr, isToday, completed };
  });

  const items = [
    {
      label: 'Drill',
      icon: Target,
      text: `${mission.drill.title} (IR: ${mission.drill.irScore}) — ${mission.drill.time}`,
      color: 'text-forge-400',
    },
    { label: 'Focus', icon: Lightbulb, text: mission.focus, color: 'text-amber-400' },
    {
      label: 'Mental Cue',
      icon: Brain,
      text: mission.mentalCue,
      color: 'text-purple-400',
    },
    { label: 'Meta Tip', icon: Zap, text: mission.metaTip, color: 'text-sky-400' },
  ];
  if (featuredWeapon) {
    items.push({
      label: 'Secret Weapon',
      icon: Zap,
      text: `Review your ${featuredWeapon.name} setup`,
      color: 'text-forge-400',
    });
  }

  return (
    <div
      className={clsx(
        'rounded-xl border p-5 transition-all',
        allComplete
          ? 'border-forge-500/40 bg-forge-950/30'
          : 'border-dark-700/50 bg-dark-900/80',
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-orange-500/10">
            <Flame className="h-5 w-5 text-orange-400" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-dark-100">
              Daily Forge — {today}
            </h2>
            <p className="text-[10px] text-dark-500">
              Complete all 4 missions to keep your streak alive
            </p>
          </div>
        </div>

        {/* Streak Badge */}
        <div className="flex items-center gap-1.5 rounded-full bg-orange-500/10 px-3 py-1">
          <Flame className="h-3.5 w-3.5 text-orange-400" />
          <span className="text-xs font-bold text-orange-400">
            Day {status.current_streak || 1}
          </span>
        </div>
      </div>

      {/* Mission Items with Checkboxes */}
      <div className="space-y-3">
        {items.map((item, idx) => {
          const Icon = item.icon;
          const checked = idx < checks.length ? checks[idx] : false;
          const isDrill = idx === 0;
          const inProgress = isDrill && meta.drillInProgress && !checked;

          return (
            <div
              key={item.label}
              className={clsx(
                'flex items-start gap-3 rounded-lg border px-3 py-2.5 transition-all',
                checked && 'border-forge-500/30 bg-forge-950/20',
                !checked && inProgress && 'border-amber-500/40 bg-amber-950/20',
                !checked && !inProgress && 'border-dark-700/40 bg-dark-800/50',
              )}
            >
              <button
                onClick={() => toggleCheck(idx)}
                className="mt-0.5 flex-shrink-0"
                aria-label={
                  checked
                    ? `Mark ${item.label} incomplete`
                    : `Mark ${item.label} complete`
                }
              >
                {checked ? (
                  <CheckCircle2 className="h-4 w-4 text-forge-400" />
                ) : inProgress ? (
                  <Loader2 className="h-4 w-4 animate-spin text-amber-400" />
                ) : (
                  <Circle className="h-4 w-4 text-dark-600" />
                )}
              </button>
              <button
                type="button"
                onClick={isDrill ? handleDrillClick : () => toggleCheck(idx)}
                disabled={checked}
                className="flex-1 min-w-0 text-left disabled:cursor-default"
                aria-label={isDrill ? 'Start drill' : `Acknowledge ${item.label}`}
              >
                <div className="flex items-center gap-2 mb-0.5">
                  <Icon className={clsx('h-3.5 w-3.5', item.color)} />
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-dark-400">
                    {item.label}
                  </span>
                  {inProgress && (
                    <span className="text-[10px] font-semibold text-amber-400">
                      In progress
                    </span>
                  )}
                </div>
                <p
                  className={clsx(
                    'text-xs leading-relaxed transition-colors',
                    checked && 'text-dark-500 line-through',
                    !checked && inProgress && 'text-amber-200',
                    !checked && !inProgress && 'text-dark-200',
                  )}
                >
                  {item.text}
                </p>
              </button>
            </div>
          );
        })}
      </div>

      {/* Streak Calendar */}
      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-1">
          {calendarDots.map((dot) => (
            <div
              key={dot.dateStr}
              className={clsx(
                'h-2.5 w-2.5 rounded-full transition-all',
                dot.completed && 'bg-forge-400',
                !dot.completed && dot.isToday && 'border border-dark-500 bg-dark-800',
                !dot.completed && !dot.isToday && 'bg-dark-700/50',
              )}
              title={dot.dateStr}
            />
          ))}
        </div>

        {/* Generate New */}
        <button
          onClick={regenerate}
          className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[10px] font-medium text-dark-400 transition-colors hover:bg-dark-800 hover:text-dark-200"
        >
          <RefreshCw className="h-3 w-3" />
          Generate New
        </button>
      </div>

      {/* Complete State */}
      {allComplete && (
        <div className="mt-4 flex flex-col items-center justify-center gap-1 rounded-lg border border-forge-500/30 bg-forge-500/10 px-4 py-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-forge-400" />
            <span className="text-xs font-semibold text-forge-400">
              Daily Forge Complete &#10003;
            </span>
          </div>
          <span className="text-[10px] text-dark-400">
            PlayerTwin updated — streak maintained
          </span>
        </div>
      )}

      {/* Streak toast */}
      {toastMessage && (
        <div
          role="status"
          className="fixed bottom-6 right-6 z-50 rounded-lg border border-forge-500/40 bg-dark-900/95 px-4 py-2.5 shadow-lg"
        >
          <p className="text-xs font-semibold text-forge-400">{toastMessage}</p>
        </div>
      )}
    </div>
  );
}

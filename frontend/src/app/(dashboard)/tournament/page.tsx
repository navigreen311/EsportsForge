/**
 * TournaOps — Tournament Operations Console.
 * Real-time tournament management with bracket viewer, opponent queue,
 * warmup checklist, memory cards, session health, and fast note entry.
 */

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Trophy,
  Clock,
  Users,
  CheckSquare,
  Brain,
  StickyNote,
  Gamepad2,
  Timer,
  Activity,
  ShieldOff,
  ChevronRight,
  ChevronDown,
  AlertTriangle,
  Zap,
  Target,
  Mic,
  Droplets,
  X,
  Plus,
  Wifi,
  Play,
  Pause,
} from 'lucide-react';
import { useVoiceForge } from '@/hooks/useVoiceForge';

// --- Helpers ---
const slug = (name: string) => name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

// --- Mock Data ---

const TOURNAMENT = {
  name: 'Friday Night Lights Championship',
  bracketPosition: 'Winners Round 3',
  record: '4-1',
  nextOpponent: 'xViper_Elite',
  nextMatchTime: new Date(Date.now() + 42 * 60 * 1000), // 42 min from now
  seed: 3,
  totalPlayers: 32,
  prizePool: '$5,000',
  structure: 'Double Elimination',
  matchTimeLimit: '12 minutes per quarter',
  bannedPlays: ['QB Spy Glitch', 'Trips TE Bunch Cheese'],
  rulesUrl: '/rules/friday-night-lights',
};

const RECORD_BREAKDOWN = [
  { round: 'R1', result: 'Won', score: '28-14', opponent: 'Player16' },
  { round: 'R2', result: 'Won', score: '21-17', opponent: 'ColdRead99' },
  { round: 'R3', result: 'Pending', score: '—', opponent: 'xViper_Elite' },
];

const COUNTER_PACKAGE_BLITZ = {
  archetype: 'Blitz Heavy',
  plays: [
    { name: 'Shotgun Trips — Slip Screen', why: 'Punish overcommitted edge rushers', confidence: 92 },
    { name: 'Singleback Ace — Hot Slants', why: 'Quick-game release vs A-gap blitz', confidence: 88 },
    { name: 'Gun Empty — Mesh Concept', why: 'Rub routes vs man under blitz', confidence: 85 },
    { name: 'Pistol Strong — Max Protect Shot', why: 'Keep TE+RB in, isolate WR1 deep', confidence: 81 },
  ],
  defensiveScheme: 'Cover 1 Robber — single-high safety with hook player to disrupt crossers',
  preSnapTips: [
    'Watch the late-rotating safety — Cover 1 reveal',
    'Count the box: 6+ defenders = blitz cue',
    'Mike LB walking up = A-gap pressure',
  ],
};

const BENCHMARK_BREAKDOWN = [
  { archetype: 'Aggressive Rush', games: 18, winRate: 67 },
  { archetype: 'Zone Coverage', games: 22, winRate: 59 },
  { archetype: 'Blitz Heavy', games: 15, winRate: 48 },
  { archetype: 'West Coast', games: 11, winRate: 73 },
  { archetype: 'Spread Option', games: 9, winRate: 56 },
];

const OPPONENT_QUEUE = [
  { name: 'xViper_Elite', archetype: 'Aggressive Rush', prep: 'ready', winRate: 62 },
  { name: 'ColdRead99', archetype: 'Zone Coverage', prep: 'partial', winRate: 55 },
  { name: 'BlitzKing_', archetype: 'Blitz Heavy', prep: 'ready', winRate: 48 },
  { name: 'SchemeMaster', archetype: 'West Coast', prep: 'none', winRate: 70 },
  { name: 'LabRat420', archetype: 'Spread Option', prep: 'partial', winRate: 58 },
];

const BRACKET_ROUNDS: { round: string; matchups: { players: [string, string]; sourceMatch?: string; expectedTime?: string }[] }[] = [
  { round: 'R1', matchups: [{ players: ['You (W)', 'Player16'] }, { players: ['xViper_Elite (W)', 'Player15'] }] },
  { round: 'R2', matchups: [{ players: ['You (W)', 'ColdRead99'] }, { players: ['xViper_Elite (W)', 'BlitzKing_'] }] },
  { round: 'R3', matchups: [{ players: ['You', 'xViper_Elite'], expectedTime: '8:42 PM' }] },
  { round: 'Final', matchups: [{ players: ['TBD', 'TBD'], sourceMatch: 'R3', expectedTime: '9:30 PM' }] },
];

const WARMUP_CHECKLIST_ITEMS = [
  { id: 'schemes', label: 'Opponent schemes reviewed', default: true },
  { id: 'drills', label: 'Pre-match drills completed', default: true },
  { id: 'mental', label: 'Mental state check — focused', default: false },
  { id: 'killsheet', label: 'Kill sheet loaded', default: false },
  { id: 'hydration', label: 'Hydrated + bathroom break', default: false },
  { id: 'equipment', label: 'Equipment checked (controller battery, mic)', default: false },
];

const WARMUP_STORAGE_KEY = 'esf:tournament:warmup';

type MemoryBullet = { text: string; evidence: string; sampleSize: number; confidence: number };
const MEMORY_CARDS: Record<string, MemoryBullet[]> = {
  'xViper_Elite': [
    { text: 'Runs cover-3 on 1st down 80%', evidence: 'Across 41 1st-down snaps in last 5 sessions', sampleSize: 41, confidence: 92 },
    { text: 'Blitzes on 3rd & long from nickel', evidence: 'Blitz rate 71% on 3rd & 7+', sampleSize: 24, confidence: 84 },
    { text: 'Goes for it on 4th in opponent territory', evidence: '7/9 4th-down attempts in opp 40', sampleSize: 9, confidence: 76 },
  ],
  'ColdRead99': [
    { text: 'Heavy zone, rarely man', evidence: 'Zone coverage 89% of dropbacks', sampleSize: 110, confidence: 95 },
    { text: 'Uses Tampa 2 shell in redzone', evidence: 'Tampa 2 on 6/8 RZ snaps last game', sampleSize: 8, confidence: 65 },
    { text: 'Audibles out of base on motion', evidence: 'Reacts to motion 78% of the time', sampleSize: 32, confidence: 81 },
  ],
  'BlitzKing_': [
    { text: 'Fire zone on 2nd & long', evidence: 'Fire zone 69% on 2nd & 8+', sampleSize: 29, confidence: 88 },
    { text: 'Man coverage outside', evidence: 'Outside CB man 73%', sampleSize: 64, confidence: 90 },
    { text: 'Vulnerable to TE seam routes', evidence: 'Allowed 6 TE seam catches in 4 games', sampleSize: 6, confidence: 72 },
  ],
};

// Task 2G: confidence scores added
const GAMEPLAN = [
  { id: 1, play: 'Gun Trips TE — Mesh Spot', situation: '1st & 10', note: 'Beats Cover 3', confidence: 94 },
  { id: 2, play: 'Singleback Ace — PA Crossers', situation: '2nd & Med', note: 'Cover 2 beater', confidence: 88 },
  { id: 3, play: 'Shotgun Bunch — Corner Strike', situation: 'Red Zone', note: 'Man beater', confidence: 91 },
  { id: 4, play: 'I-Form Close — HB Stretch', situation: '1st down', note: 'Run setup', confidence: 85 },
  { id: 5, play: 'Gun Empty — 4 Verts', situation: '3rd & Long', note: 'Aggressive shot', confidence: 72 },
  { id: 6, play: 'Pistol Strong — RPO Alert', situation: '2nd & Short', note: 'Read the LB', confidence: 80 },
  { id: 7, play: 'Shotgun Spread — Slants', situation: '3rd & Med', note: 'Quick game', confidence: 93 },
  { id: 8, play: 'Singleback Wing — Counter', situation: '1st & 10', note: 'Misdirection', confidence: 78 },
  { id: 9, play: 'Gun Bunch — Levels Sail', situation: '2nd & Long', note: 'Zone flood', confidence: 87 },
  { id: 10, play: 'Empty Trey — Stick Nod', situation: '3rd & Short', note: 'Easy conversion', confidence: 96 },
  { id: 11, play: 'I-Form — PA Boot', situation: 'Opening script', note: 'Test deep', confidence: 83 },
  { id: 12, play: 'Shotgun Trips — Screen', situation: 'Blitz response', note: 'Punish pressure', confidence: 90 },
  { id: 13, play: 'Gun Doubles — Dagger', situation: 'Cover 2', note: 'Post-dig combo', confidence: 76 },
  { id: 14, play: 'Singleback — Inside Zone', situation: 'Clock control', note: 'Safe yards', confidence: 98 },
  { id: 15, play: 'Hail Mary / Scramble', situation: '2-min desperation', note: 'Last resort', confidence: 70 },
];

type ClockNode = {
  time: string;
  seconds: number;
  condition: string;
  action: string;
  sequence: string[];
  decisionTree: { ifBranch: string; thenAction: string }[];
  audibles: string[];
};
const CLOCK_TREE: ClockNode[] = [
  {
    time: '2:00', seconds: 120, condition: 'Down 3+', action: 'No huddle, attack sidelines',
    sequence: ['Gun Trips — Sail concept', 'Gun Empty — Mesh', 'Gun Doubles — Smash'],
    decisionTree: [
      { ifBranch: 'Cover 2', thenAction: 'Smash to fade-flat' },
      { ifBranch: 'Man press', thenAction: 'Mesh rub' },
      { ifBranch: 'Cover 3', thenAction: 'Sail flood' },
    ],
    audibles: ['Kill to Slip Screen vs blitz', 'Check to PA Boot if box >= 7'],
  },
  {
    time: '1:30', seconds: 90, condition: 'Need TD', action: 'Aggressive — 4 verts / crossers',
    sequence: ['Gun Empty — 4 Verts', 'Gun Trips — Levels', 'Gun Bunch — Crossers'],
    decisionTree: [
      { ifBranch: 'MOFC (single high)', thenAction: 'Seam to slot' },
      { ifBranch: 'MOFO (Cover 2)', thenAction: 'Levels dig at 12' },
    ],
    audibles: ['Kill to Slants vs heavy blitz'],
  },
  {
    time: '1:00', seconds: 60, condition: 'In FG range', action: 'Run clock, kick at :05',
    sequence: ['HB Inside Zone', 'QB Kneel — clock to :05', 'FG Unit'],
    decisionTree: [
      { ifBranch: 'Have all 3 TOs', thenAction: 'One more shot for TD' },
      { ifBranch: '0 TOs', thenAction: 'Kneel + spike at :05' },
    ],
    audibles: [],
  },
  {
    time: '0:30', seconds: 30, condition: 'Need TD still', action: 'Endzone shots only',
    sequence: ['Gun Empty — Fade-Flat', 'Gun Trey — Corner Strike', 'Hail Mary if last'],
    decisionTree: [
      { ifBranch: 'Have a TO', thenAction: 'Take 2 shots' },
      { ifBranch: '0 TOs', thenAction: 'Sideline routes only' },
    ],
    audibles: ['Kill to Spike if WRs not set'],
  },
  {
    time: '0:10', seconds: 10, condition: 'Any', action: 'Spike or timeout, last play',
    sequence: ['Spike OR Hail Mary'],
    decisionTree: [
      { ifBranch: 'Down by <8', thenAction: 'Hail Mary' },
      { ifBranch: 'Need FG', thenAction: 'Spike then kick' },
    ],
    audibles: [],
  },
];

const RESET_STEPS = [
  { step: 1, text: 'Close eyes, 4 deep breaths (box breathing)' },
  { step: 2, text: 'Name 1 thing you did well last game' },
  { step: 3, text: 'Identify 1 adjustment for next game' },
  { step: 4, text: 'Visualize your opening script executing' },
  { step: 5, text: 'Reset posture — shoulders back, hands loose' },
];

// Task 2G helper
function confidenceColor(c: number): string {
  if (c >= 90) return '#4ADE80';
  if (c >= 75) return 'white';
  return '#F59E0B';
}

export default function TournamentPage() {
  const router = useRouter();
  const voice = useVoiceForge();

  const [countdown, setCountdown] = useState('');
  const [countdownLevel, setCountdownLevel] = useState<'normal' | 'warn' | 'critical' | 'live'>('normal');
  const [showRulesModal, setShowRulesModal] = useState(false);
  const [showRecordSlideOver, setShowRecordSlideOver] = useState(false);
  const [showCounterPackage, setShowCounterPackage] = useState(false);
  const [showBenchmark, setShowBenchmark] = useState(false);
  const [counterToast, setCounterToast] = useState<string | null>(null);
  const [bulletDetail, setBulletDetail] = useState<{ opponent: string; bullet: MemoryBullet } | null>(null);
  const [showAddMemoryCard, setShowAddMemoryCard] = useState(false);
  const [newCardOpponent, setNewCardOpponent] = useState<string>(OPPONENT_QUEUE[0].name);
  const [newCardText, setNewCardText] = useState('');
  const [customCards, setCustomCards] = useState<Record<string, MemoryBullet[]>>({});
  const [playDetail, setPlayDetail] = useState<typeof GAMEPLAN[number] | null>(null);
  const [gameplanFilter, setGameplanFilter] = useState<'all' | 'cover3' | 'redzone' | '3rd' | '2min'>('all');
  const [clockNodeDetail, setClockNodeDetail] = useState<ClockNode | null>(null);
  const [drillModeActive, setDrillModeActive] = useState(false);
  const [drillModeRemaining, setDrillModeRemaining] = useState(120);

  // C11: 2-Minute Drill Mode timer
  useEffect(() => {
    if (!drillModeActive) return;
    const interval = setInterval(() => {
      setDrillModeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          setDrillModeActive(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [drillModeActive]);

  const activeClockIndex = drillModeActive
    ? CLOCK_TREE.findIndex((n, i) => drillModeRemaining <= n.seconds && (i === CLOCK_TREE.length - 1 || drillModeRemaining > CLOCK_TREE[i + 1].seconds))
    : -1;
  const [matchStartTriggered, setMatchStartTriggered] = useState(false);
  const oneMinPulseRef = useRef(false);
  const [checklist, setChecklist] = useState<Record<string, boolean>>(
    Object.fromEntries(WARMUP_CHECKLIST_ITEMS.map((i) => [i.id, i.default]))
  );
  const [showResetChecklistConfirm, setShowResetChecklistConfirm] = useState(false);
  const [warmupToast, setWarmupToast] = useState<string | null>(null);

  // Hydrate from localStorage on mount, persist on change
  useEffect(() => {
    try {
      const raw = localStorage.getItem(WARMUP_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Record<string, boolean>;
        setChecklist((prev) => ({ ...prev, ...parsed }));
      }
    } catch { /* ignore */ }
  }, []);
  useEffect(() => {
    try { localStorage.setItem(WARMUP_STORAGE_KEY, JSON.stringify(checklist)); } catch { /* ignore */ }
  }, [checklist]);
  const [notes, setNotes] = useState<{ id: string; time: string; text: string }[]>([]);
  const [noteInput, setNoteInput] = useState('');
  const [failsafeMode, setFailsafeMode] = useState(false);
  const [tiltStatus, setTiltStatus] = useState<'green' | 'yellow' | 'red'>('green');
  const [fatigue, setFatigue] = useState(28);
  const [breakTimer, setBreakTimer] = useState(12);

  // Task 2A: expanded opponent in queue
  const [expandedOpponent, setExpandedOpponent] = useState<string | null>(null);

  // Task 2B: between-round reset state
  const [resetSteps, setResetSteps] = useState([false, false, false, false, false]);
  const [breathingActive, setBreathingActive] = useState(false);
  const [breathTimer, setBreathTimer] = useState(30);
  const [breathPhase, setBreathPhase] = useState('Inhale');

  // Task 2E: hydration reminder
  const [showHydration, setShowHydration] = useState(false);
  const hydrationShown = useRef(false);

  const resetSectionRef = useRef<HTMLDivElement>(null);

  // Countdown timer + hydration + auto-nav at 0:00 (Task 2E + C1)
  useEffect(() => {
    const playTone = () => {
      try {
        const ctx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain); gain.connect(ctx.destination);
        osc.frequency.value = 880; gain.gain.value = 0.05;
        osc.start(); osc.stop(ctx.currentTime + 0.2);
      } catch { /* audio unavailable */ }
    };

    const interval = setInterval(() => {
      const diff = TOURNAMENT.nextMatchTime.getTime() - Date.now();
      if (diff <= 0) {
        setCountdown('LIVE NOW');
        setCountdownLevel('live');
        if (!hydrationShown.current) {
          setShowHydration(true);
          hydrationShown.current = true;
        }
        if (!matchStartTriggered) {
          setMatchStartTriggered(true);
          // Match start — auto-navigate to war room with the next opponent
          router.push(`/war-room?opponent=${slug(TOURNAMENT.nextOpponent)}`);
        }
      } else {
        const m = Math.floor(diff / 60000);
        const s = Math.floor((diff % 60000) / 1000);
        setCountdown(`${m}:${s.toString().padStart(2, '0')}`);
        if (diff <= 60_000) {
          setCountdownLevel('critical');
          if (!oneMinPulseRef.current) {
            oneMinPulseRef.current = true;
            playTone();
          }
        } else if (diff <= 5 * 60_000) {
          setCountdownLevel('warn');
        } else {
          setCountdownLevel('normal');
        }
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [router, matchStartTriggered]);

  // Task 2E: auto-dismiss hydration after 8s
  useEffect(() => {
    if (!showHydration) return;
    const t = setTimeout(() => setShowHydration(false), 8000);
    return () => clearTimeout(t);
  }, [showHydration]);

  // Task 2B: breathing timer
  useEffect(() => {
    if (!breathingActive) return;

    const phases = ['Inhale', 'Hold', 'Exhale', 'Hold'];
    let elapsed = 0;

    const interval = setInterval(() => {
      elapsed += 1;
      const remaining = 30 - elapsed;
      setBreathTimer(remaining);

      // Cycle phases every 4 seconds
      const phaseIndex = Math.floor(elapsed / 4) % 4;
      setBreathPhase(phases[phaseIndex]);

      if (remaining <= 0) {
        clearInterval(interval);
        setBreathingActive(false);
        setBreathTimer(30);
        setBreathPhase('Inhale');
        // Auto-check step 1
        setResetSteps((prev) => {
          const next = [...prev];
          next[0] = true;
          return next;
        });
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [breathingActive]);

  const addNote = async () => {
    const trimmed = noteInput.trim();
    if (!trimmed) return;
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const localId = `local-${Date.now()}`;
    setNotes((prev) => [{ id: localId, time, text: trimmed }, ...prev]);
    setNoteInput('');
    // Persist to vault — best-effort
    const session = await import('next-auth/react').then((m) => m.getSession());
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';
    try {
      const res = await fetch(`${apiBase}/api/v1/vault/entries`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(session?.accessToken ? { Authorization: `Bearer ${session.accessToken}` } : {}),
        },
        body: JSON.stringify({
          title: `Tournament Note — ${TOURNAMENT.name} — ${time}`,
          category: 'Tournament Note',
          tournament_id: TOURNAMENT.name,
          content: trimmed,
        }),
      });
      if (res.ok) {
        const body = await res.json().catch(() => null);
        const remoteId = body?.id || body?.entry_id;
        if (remoteId) {
          setNotes((prev) => prev.map((n) => (n.id === localId ? { ...n, id: String(remoteId) } : n)));
        }
      }
    } catch { /* offline / failed — keep local note */ }
  };

  const deleteNote = async (id: string) => {
    setNotes((prev) => prev.filter((n) => n.id !== id));
    if (id.startsWith('local-')) return;
    const session = await import('next-auth/react').then((m) => m.getSession());
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';
    fetch(`${apiBase}/api/v1/vault/entries/${id}`, {
      method: 'DELETE',
      headers: { ...(session?.accessToken ? { Authorization: `Bearer ${session.accessToken}` } : {}) },
    }).catch(() => {});
  };

  const resetComplete = resetSteps.every(Boolean);
  const resetCount = resetSteps.filter(Boolean).length;

  // C7: when reset transitions to 5/5, fire side effects (toast, mood, fatigue drop, auto-nav)
  const resetCompleteFiredRef = useRef(false);
  useEffect(() => {
    if (resetComplete && !resetCompleteFiredRef.current) {
      resetCompleteFiredRef.current = true;
      setTiltStatus('green');
      setFatigue((f) => Math.max(0, f - 12));
      setWarmupToast("Reset complete — you're ready");
      setTimeout(() => setWarmupToast(null), 3500);
      // Persist to TiltGuard backend (best-effort)
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';
      fetch(`${apiBase}/api/v1/tiltguard/reset-logged`, { method: 'POST' }).catch(() => {});
      // Auto-nav to next-round prep after a brief delay
      setTimeout(() => {
        const next = OPPONENT_QUEUE[0];
        router.push(`/war-room?opponent=${slug(next.name)}`);
      }, 2500);
    }
    if (!resetComplete) resetCompleteFiredRef.current = false;
  }, [resetComplete, router]);

  // Task 2C: voice command handlers (also bound to clickable pills, C2)
  const speakBriefing = useCallback(() => {
    const firstOpp = OPPONENT_QUEUE[0];
    const cards = MEMORY_CARDS[firstOpp.name];
    const text = cards
      ? `Next opponent: ${firstOpp.name}. ${firstOpp.archetype}. ${cards.map((c) => c.text).join('. ')}`
      : `Next opponent: ${firstOpp.name}. ${firstOpp.archetype}.`;
    voice.speak(text);
  }, [voice]);

  const startReset = useCallback(() => {
    resetSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
    setBreathingActive(true);
  }, []);

  const speakRecord = useCallback(() => {
    const wins = RECORD_BREAKDOWN.filter((r) => r.result === 'Won').map((r) => r.round).join(', ');
    const next = RECORD_BREAKDOWN.find((r) => r.result === 'Pending');
    const minutes = Math.max(0, Math.floor((TOURNAMENT.nextMatchTime.getTime() - Date.now()) / 60000));
    const nextLine = next ? ` ${next.round} is in ${minutes} minutes vs ${next.opponent}.` : '';
    voice.speak(
      `Record ${TOURNAMENT.record.replace('-', ' and ')}. You've won ${wins || 'none yet'}.${nextLine} Bracket position: top ${Math.max(4, TOURNAMENT.totalPlayers / 8)}.`
    );
  }, [voice]);

  const handleVoiceCommand = useCallback(async () => {
    const transcript = await voice.listen({ timeout: 5000 });
    const cmd = transcript.toLowerCase().trim();
    if (cmd.includes('read next briefing') || cmd.includes('next opponent')) speakBriefing();
    else if (cmd.includes('start reset') || cmd.includes('mental reset')) startReset();
    else if (cmd.includes('my record') || cmd.includes("what's my record")) speakRecord();
  }, [voice, speakBriefing, startReset, speakRecord]);

  // Task 2F: bracket intelligence
  const hardestOpponent = OPPONENT_QUEUE.reduce((min, opp) => opp.winRate < min.winRate ? opp : min, OPPONENT_QUEUE[0]);
  const winRates = OPPONENT_QUEUE.map((o) => o.winRate);
  const maxRate = Math.max(...winRates);
  const minRate = Math.min(...winRates);
  const allWithinRange = (maxRate - minRate) <= 10;

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-forge-500/15">
              <Trophy className="h-6 w-6 text-forge-400" />
            </div>
            <div>
              <button
                type="button"
                onClick={() => setShowRulesModal(true)}
                className="text-2xl font-bold text-dark-50 hover:text-forge-300 transition-colors text-left"
              >
                {TOURNAMENT.name}
              </button>
              <p className="text-sm text-dark-400">
                {TOURNAMENT.bracketPosition} &middot; Record:{' '}
                <button
                  type="button"
                  onClick={() => setShowRecordSlideOver(true)}
                  className="text-dark-200 hover:text-forge-400 underline-offset-2 hover:underline transition-colors"
                >
                  {TOURNAMENT.record}
                </button>{' '}
                &middot; Seed #{TOURNAMENT.seed}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <button
              type="button"
              onClick={() => router.push(`/opponents/${slug(TOURNAMENT.nextOpponent)}`)}
              className="rounded-lg bg-dark-800 px-4 py-2 text-left hover:bg-dark-700 transition-colors"
            >
              <p className="text-xs text-dark-400">Next Opponent</p>
              <p className="text-sm font-semibold text-dark-50 hover:text-forge-300">{TOURNAMENT.nextOpponent}</p>
            </button>
            <div
              className={`rounded-lg px-4 py-2 border transition-colors ${
                countdownLevel === 'critical'
                  ? 'bg-red-500/10 border-red-500/40 animate-pulse'
                  : countdownLevel === 'warn'
                  ? 'bg-amber-500/10 border-amber-500/30'
                  : countdownLevel === 'live'
                  ? 'bg-green-500/15 border-green-500/40'
                  : 'bg-forge-500/10 border-forge-500/20'
              }`}
            >
              <p className={`text-xs ${
                countdownLevel === 'critical' ? 'text-red-400' :
                countdownLevel === 'warn' ? 'text-amber-400' :
                countdownLevel === 'live' ? 'text-green-400' :
                'text-forge-400'
              }`}>Countdown</p>
              <p className={`text-lg font-bold font-mono ${
                countdownLevel === 'critical' ? 'text-red-400' :
                countdownLevel === 'warn' ? 'text-amber-400' :
                countdownLevel === 'live' ? 'text-green-400' :
                'text-forge-400'
              }`}>{countdown || '--:--'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tournament rules modal (C1) */}
      {showRulesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setShowRulesModal(false)}>
          <div className="w-full max-w-lg rounded-xl border border-dark-700 bg-dark-900 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-lg font-bold text-dark-50">{TOURNAMENT.name}</h3>
              <button onClick={() => setShowRulesModal(false)} className="text-dark-500 hover:text-dark-200"><X className="h-5 w-5" /></button>
            </div>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <dt className="text-dark-400">Prize Pool</dt><dd className="text-dark-100 font-semibold">{TOURNAMENT.prizePool}</dd>
              <dt className="text-dark-400">Bracket Structure</dt><dd className="text-dark-100">{TOURNAMENT.structure}</dd>
              <dt className="text-dark-400">Time Limit</dt><dd className="text-dark-100">{TOURNAMENT.matchTimeLimit}</dd>
              <dt className="text-dark-400">Players</dt><dd className="text-dark-100">{TOURNAMENT.totalPlayers}</dd>
            </dl>
            <div className="mt-4">
              <p className="text-xs font-semibold text-dark-300 mb-1">Banned Plays / Exploits</p>
              <ul className="text-xs text-dark-400 space-y-0.5">
                {TOURNAMENT.bannedPlays.map((p) => <li key={p}>&middot; {p}</li>)}
              </ul>
            </div>
            <div className="mt-5 flex justify-end">
              <a
                href={TOURNAMENT.rulesUrl}
                className="rounded-lg border border-forge-500/40 bg-forge-500/10 px-4 py-2 text-sm font-semibold text-forge-400 hover:bg-forge-500/20"
              >
                View Full Tournament Rules &rarr;
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Round-by-round record slide-over (C1) */}
      {showRecordSlideOver && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60" onClick={() => setShowRecordSlideOver(false)}>
          <div className="h-full w-full max-w-md border-l border-dark-700 bg-dark-900 p-6 overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-lg font-bold text-dark-50">Round-by-round Record</h3>
              <button onClick={() => setShowRecordSlideOver(false)} className="text-dark-500 hover:text-dark-200"><X className="h-5 w-5" /></button>
            </div>
            <div className="space-y-2">
              {RECORD_BREAKDOWN.map((r) => (
                <div key={r.round} className="flex items-center justify-between rounded-lg bg-dark-800/60 p-3">
                  <div>
                    <p className="text-sm font-semibold text-dark-100">{r.round}: {r.result === 'Won' ? `Won ${r.score}` : r.result}</p>
                    <p className="text-xs text-dark-400">vs {r.opponent}</p>
                  </div>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                    r.result === 'Won' ? 'bg-green-500/15 text-green-400' :
                    r.result === 'Lost' ? 'bg-red-500/15 text-red-400' :
                    'bg-amber-500/15 text-amber-400'
                  }`}>{r.result}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Bracket Intelligence Counter Package slide-over (C5) */}
      {showCounterPackage && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60" onClick={() => setShowCounterPackage(false)}>
          <div className="h-full w-full max-w-lg border-l border-dark-700 bg-dark-900 p-6 overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold text-dark-50">Counter Package</h3>
                <p className="text-xs text-dark-400 mt-0.5">vs {COUNTER_PACKAGE_BLITZ.archetype}</p>
              </div>
              <button onClick={() => setShowCounterPackage(false)} className="text-dark-500 hover:text-dark-200"><X className="h-5 w-5" /></button>
            </div>
            <p className="text-xs font-semibold text-dark-300 uppercase mb-2">Plays that beat blitz</p>
            <div className="space-y-2 mb-5">
              {COUNTER_PACKAGE_BLITZ.plays.map((p) => (
                <div key={p.name} className="rounded-lg bg-dark-800/60 p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-dark-100">{p.name}</p>
                    <span className="text-xs font-bold tabular-nums" style={{ color: confidenceColor(p.confidence) }}>{p.confidence}%</span>
                  </div>
                  <p className="text-xs text-dark-400 mt-0.5">{p.why}</p>
                </div>
              ))}
            </div>
            <p className="text-xs font-semibold text-dark-300 uppercase mb-1">Defensive Recommendation</p>
            <p className="text-sm text-dark-200 mb-4">{COUNTER_PACKAGE_BLITZ.defensiveScheme}</p>
            <p className="text-xs font-semibold text-dark-300 uppercase mb-1">Pre-snap Recognition</p>
            <ul className="space-y-1 mb-5">
              {COUNTER_PACKAGE_BLITZ.preSnapTips.map((t) => (
                <li key={t} className="text-xs text-dark-300 flex items-start gap-2">
                  <ChevronRight className="h-3 w-3 mt-0.5 text-forge-400 flex-shrink-0" />{t}
                </li>
              ))}
            </ul>
            <div className="flex gap-2 pt-3 border-t border-dark-700/50">
              <button
                type="button"
                onClick={() => {
                  fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001'}/api/v1/gameplans/append`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source: 'tournament-counter-package', plays: COUNTER_PACKAGE_BLITZ.plays.map((p) => p.name) }),
                  }).catch(() => {});
                  setCounterToast('Added 4 plays to gameplan');
                  setShowCounterPackage(false);
                  setTimeout(() => setCounterToast(null), 3500);
                }}
                className="flex-1 rounded-lg bg-forge-500/15 px-3 py-2 text-xs font-semibold text-forge-400 hover:bg-forge-500/25"
              >
                Add All to Gameplan
              </button>
              <button
                type="button"
                onClick={() => {
                  fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001'}/api/v1/vault/entries`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      title: `Counter Package — ${COUNTER_PACKAGE_BLITZ.archetype}`,
                      category: 'Counter Package',
                      content: JSON.stringify(COUNTER_PACKAGE_BLITZ),
                    }),
                  }).catch(() => {});
                  setCounterToast('Saved to Vault');
                  setShowCounterPackage(false);
                  setTimeout(() => setCounterToast(null), 3500);
                }}
                className="flex-1 rounded-lg border border-dark-600 bg-dark-800 px-3 py-2 text-xs font-semibold text-dark-200 hover:bg-dark-700"
              >
                Save to Vault
              </button>
            </div>
          </div>
        </div>
      )}

      {/* BenchmarkAI win-rate breakdown modal (C5) */}
      {showBenchmark && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setShowBenchmark(false)}>
          <div className="w-full max-w-md rounded-xl border border-dark-700 bg-dark-900 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold text-dark-50">BenchmarkAI</h3>
                <p className="text-xs text-dark-400">Win rate vs each archetype, last 30 days</p>
              </div>
              <button onClick={() => setShowBenchmark(false)} className="text-dark-500 hover:text-dark-200"><X className="h-5 w-5" /></button>
            </div>
            <div className="space-y-2">
              {BENCHMARK_BREAKDOWN.map((b) => (
                <div key={b.archetype}>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-dark-200 font-medium">{b.archetype}</span>
                    <span className="text-dark-400">{b.winRate}% &middot; {b.games} games</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-dark-800 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${b.winRate >= 60 ? 'bg-green-500' : b.winRate >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                      style={{ width: `${b.winRate}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Counter package toast (C5) */}
      {counterToast && (
        <div className="fixed bottom-6 right-6 z-50 rounded-lg border border-forge-500/40 bg-dark-900 px-4 py-3 text-sm text-forge-300 shadow-lg">
          {counterToast}
        </div>
      )}

      {/* Reset Checklist confirm modal (C6) */}
      {showResetChecklistConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setShowResetChecklistConfirm(false)}>
          <div className="w-full max-w-sm rounded-xl border border-dark-700 bg-dark-900 p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-dark-50 mb-1">Reset all warmup items?</h3>
            <p className="text-sm text-dark-400 mb-5">All {WARMUP_CHECKLIST_ITEMS.length} checkboxes will be cleared.</p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowResetChecklistConfirm(false)}
                className="rounded-lg border border-dark-600 bg-dark-800 px-4 py-2 text-sm text-dark-200 hover:bg-dark-700"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setChecklist(Object.fromEntries(WARMUP_CHECKLIST_ITEMS.map((i) => [i.id, false])));
                  setShowResetChecklistConfirm(false);
                  setWarmupToast('Warmup checklist reset');
                  setTimeout(() => setWarmupToast(null), 3000);
                }}
                className="rounded-lg bg-amber-500/15 border border-amber-500/40 px-4 py-2 text-sm font-semibold text-amber-300 hover:bg-amber-500/25"
              >
                Reset
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Warmup toast (C6) */}
      {warmupToast && (
        <div className="fixed bottom-6 right-6 z-50 rounded-lg border border-forge-500/40 bg-dark-900 px-4 py-3 text-sm text-forge-300 shadow-lg">
          {warmupToast}
        </div>
      )}

      {/* Memory bullet detail modal (C8) */}
      {bulletDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setBulletDetail(null)}>
          <div className="w-full max-w-md rounded-xl border border-dark-700 bg-dark-900 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-xs text-dark-400">{bulletDetail.opponent}</p>
                <h3 className="text-base font-semibold text-dark-50">{bulletDetail.bullet.text}</h3>
              </div>
              <button onClick={() => setBulletDetail(null)} className="text-dark-500 hover:text-dark-200"><X className="h-5 w-5" /></button>
            </div>
            <p className="text-sm text-dark-300 mb-4">{bulletDetail.bullet.evidence}</p>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-lg bg-dark-800/60 p-3">
                <p className="text-xs text-dark-400">Sample size</p>
                <p className="text-lg font-bold text-dark-100">{bulletDetail.bullet.sampleSize}</p>
              </div>
              <div className="rounded-lg bg-dark-800/60 p-3">
                <p className="text-xs text-dark-400">Confidence</p>
                <p className="text-lg font-bold" style={{ color: confidenceColor(bulletDetail.bullet.confidence) }}>{bulletDetail.bullet.confidence}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 2-Minute Drill Tree node detail modal (C11) */}
      {clockNodeDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setClockNodeDetail(null)}>
          <div className="w-full max-w-md rounded-xl border border-dark-700 bg-dark-900 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-xs text-forge-400 font-mono">{clockNodeDetail.time}</p>
                <h3 className="text-lg font-bold text-dark-50">{clockNodeDetail.action}</h3>
                <p className="text-xs text-dark-400">{clockNodeDetail.condition}</p>
              </div>
              <button onClick={() => setClockNodeDetail(null)} className="text-dark-500 hover:text-dark-200"><X className="h-5 w-5" /></button>
            </div>
            <p className="text-xs font-semibold text-dark-300 uppercase mt-4 mb-1">Play Sequence</p>
            <ol className="space-y-1 mb-4">
              {clockNodeDetail.sequence.map((s, i) => (
                <li key={i} className="text-xs text-dark-200 flex gap-2"><span className="text-dark-500 w-4">{i + 1}.</span>{s}</li>
              ))}
            </ol>
            <p className="text-xs font-semibold text-dark-300 uppercase mb-1">Decision Tree</p>
            <ul className="space-y-1 mb-4">
              {clockNodeDetail.decisionTree.map((d, i) => (
                <li key={i} className="text-xs text-dark-300"><span className="text-amber-300">If</span> {d.ifBranch} <span className="text-dark-500">→</span> <span className="text-dark-100">{d.thenAction}</span></li>
              ))}
            </ul>
            {clockNodeDetail.audibles.length > 0 && (
              <>
                <p className="text-xs font-semibold text-dark-300 uppercase mb-1">Audibles</p>
                <ul className="space-y-1 mb-4">
                  {clockNodeDetail.audibles.map((a, i) => (
                    <li key={i} className="text-xs text-dark-300 flex gap-2"><Mic className="h-3 w-3 text-forge-400 mt-0.5 flex-shrink-0" />{a}</li>
                  ))}
                </ul>
              </>
            )}
            <a
              href={`/sim-lab?scenario=2min-${clockNodeDetail.seconds}`}
              className="block w-full text-center rounded-lg bg-forge-500/15 border border-forge-500/30 px-4 py-2 text-sm font-semibold text-forge-300 hover:bg-forge-500/25"
            >
              Practice in SimLab &rarr;
            </a>
          </div>
        </div>
      )}

      {/* Play detail slide-over (C10) */}
      {playDetail && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60" onClick={() => setPlayDetail(null)}>
          <div className="h-full w-full max-w-md border-l border-dark-700 bg-dark-900 p-6 overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-xs text-dark-400">Play #{playDetail.id} &middot; {playDetail.situation}</p>
                <h3 className="text-lg font-bold text-dark-50">{playDetail.play}</h3>
              </div>
              <button onClick={() => setPlayDetail(null)} className="text-dark-500 hover:text-dark-200"><X className="h-5 w-5" /></button>
            </div>
            <div className="rounded-lg bg-dark-800/60 p-3 mb-4">
              <p className="text-xs text-dark-400 mb-1">Why it&apos;s in the gameplan</p>
              <p className="text-sm text-dark-200">{playDetail.note}</p>
            </div>
            <div className="flex items-center gap-2 mb-5">
              <span className="text-xs text-dark-400">Confidence</span>
              <div className="flex-1 h-1.5 rounded-full bg-dark-800 overflow-hidden">
                <div className="h-full" style={{ width: `${playDetail.confidence}%`, backgroundColor: confidenceColor(playDetail.confidence) }} />
              </div>
              <span className="text-sm font-bold tabular-nums" style={{ color: confidenceColor(playDetail.confidence) }}>{playDetail.confidence}%</span>
            </div>
            <a
              href={`/gameplan?opponent=${slug(TOURNAMENT.nextOpponent)}&play=${playDetail.id}`}
              className="block w-full text-center rounded-lg bg-forge-500/15 border border-forge-500/30 px-4 py-2 text-sm font-semibold text-forge-300 hover:bg-forge-500/25"
            >
              Open in Gameplan &rarr;
            </a>
          </div>
        </div>
      )}

      {/* Add Memory Card modal (C8) */}
      {showAddMemoryCard && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setShowAddMemoryCard(false)}>
          <div className="w-full max-w-md rounded-xl border border-dark-700 bg-dark-900 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-lg font-bold text-dark-50">Add Memory Card</h3>
              <button onClick={() => setShowAddMemoryCard(false)} className="text-dark-500 hover:text-dark-200"><X className="h-5 w-5" /></button>
            </div>
            <label className="block text-xs text-dark-400 mb-1">Opponent</label>
            <select
              value={newCardOpponent}
              onChange={(e) => setNewCardOpponent(e.target.value)}
              className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-100 mb-3"
            >
              {OPPONENT_QUEUE.map((o) => <option key={o.name} value={o.name}>{o.name}</option>)}
            </select>
            <label className="block text-xs text-dark-400 mb-1">Tendency note</label>
            <textarea
              value={newCardText}
              onChange={(e) => setNewCardText(e.target.value)}
              rows={3}
              placeholder="e.g. Drops out of base on motion to trips"
              className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-100 mb-4"
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowAddMemoryCard(false)} className="rounded-lg border border-dark-600 bg-dark-800 px-4 py-2 text-sm text-dark-200 hover:bg-dark-700">Cancel</button>
              <button
                disabled={!newCardText.trim()}
                onClick={() => {
                  const bullet: MemoryBullet = {
                    text: newCardText.trim(),
                    evidence: 'Manually added by player',
                    sampleSize: 0,
                    confidence: 50,
                  };
                  setCustomCards((prev) => ({ ...prev, [newCardOpponent]: [...(prev[newCardOpponent] ?? []), bullet] }));
                  // Best-effort persist to opponent dossier
                  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';
                  fetch(`${apiBase}/api/v1/opponents/${slug(newCardOpponent)}/memory-cards`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(bullet),
                  }).catch(() => {});
                  setNewCardText('');
                  setShowAddMemoryCard(false);
                  setWarmupToast('Memory card added');
                  setTimeout(() => setWarmupToast(null), 3000);
                }}
                className="rounded-lg bg-forge-500/15 border border-forge-500/40 px-4 py-2 text-sm font-semibold text-forge-300 hover:bg-forge-500/25 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Save Card
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Task 2C: VoiceForge command bar */}
      {voice.isAvailable && (
        <div className="flex items-center gap-3 rounded-xl border border-dark-700/50 bg-dark-900 px-4 py-3">
          <button
            onClick={handleVoiceCommand}
            disabled={voice.isListening}
            className={`flex h-8 w-8 items-center justify-center rounded-full transition-colors ${
              voice.isListening
                ? 'bg-red-500/20 text-red-400 animate-pulse'
                : 'bg-forge-500/15 text-forge-400 hover:bg-forge-500/25'
            }`}
          >
            <Mic className="h-4 w-4" />
          </button>
          <div className="flex flex-wrap gap-2">
            {[
              { label: 'Read next briefing', onClick: speakBriefing },
              { label: 'Start reset', onClick: startReset },
              { label: 'My record?', onClick: speakRecord },
            ].map(({ label, onClick }) => (
              <button
                key={label}
                type="button"
                onClick={onClick}
                className="rounded-full border border-dark-700 bg-dark-800 px-3 py-1 text-xs text-dark-300 hover:border-forge-500/40 hover:text-forge-300 transition-colors"
              >
                {label}
              </button>
            ))}
          </div>
          {voice.isListening && (
            <span className="ml-auto text-xs text-forge-400">Listening...</span>
          )}
        </div>
      )}

      {/* Task 2E: Hydration Reminder */}
      {showHydration && (
        <div className="rounded-xl border border-forge-400 bg-dark-800 p-5 text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Droplets className="h-5 w-5 text-forge-400" />
            <h3 className="text-lg font-bold text-dark-50">Time&#39;s Up</h3>
          </div>
          <p className="text-sm text-dark-300 mb-4">
            Drink water. Stand up. Take a breath. You&#39;re ready.
          </p>
          <button
            onClick={() => setShowHydration(false)}
            className="rounded-lg bg-forge-500/15 px-4 py-2 text-sm font-semibold text-forge-400 hover:bg-forge-500/25 transition-colors"
          >
            Got it
          </button>
        </div>
      )}

      {/* MAIN GRID */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 xl:grid-cols-3">

        {/* OPPONENT QUEUE — Task 2A */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <Users className="h-4 w-4 text-forge-400" /> Opponent Queue
          </h2>
          <div className="space-y-2">
            {OPPONENT_QUEUE.map((opp, i) => {
              const isFirst = i === 0;
              const isExpanded = expandedOpponent === opp.name;
              const cards = MEMORY_CARDS[opp.name];
              return (
                <div
                  key={opp.name}
                  className={`rounded-lg bg-dark-800/60 ${isFirst ? 'border-l-2 border-l-green-500' : ''}`}
                >
                  <div className="flex items-center gap-3 px-3 py-2">
                    <span className="text-xs font-bold text-dark-500 w-5">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => router.push(`/opponents/${slug(opp.name)}`)}
                          className="text-sm font-medium text-dark-100 truncate hover:text-forge-300 transition-colors text-left"
                        >
                          {opp.name}
                        </button>
                        {isFirst && (
                          <span className="rounded-full bg-green-500/15 border border-green-500/30 px-2 py-0.5 text-[10px] font-bold text-green-400 uppercase">
                            Next
                          </span>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => setExpandedOpponent(isExpanded ? null : opp.name)}
                        className="text-xs text-dark-400 hover:text-dark-200 flex items-center gap-1 transition-colors"
                      >
                        {opp.archetype}
                        {cards && (
                          isExpanded
                            ? <ChevronDown className="h-3 w-3 text-dark-500" />
                            : <ChevronRight className="h-3 w-3 text-dark-500" />
                        )}
                      </button>
                    </div>
                    <span className="text-xs text-dark-400">{opp.winRate}%</span>
                    <span className={`h-2 w-2 rounded-full ${
                      opp.prep === 'ready' ? 'bg-forge-400' : opp.prep === 'partial' ? 'bg-amber-400' : 'bg-red-400'
                    }`} title={`Prep: ${opp.prep === 'ready' ? 'Dossier complete' : opp.prep === 'partial' ? 'Partial dossier' : 'Minimal data'}`} />
                    <button
                      onClick={() => router.push(`/war-room?opponent=${slug(opp.name)}`)}
                      className="rounded-full border border-green-500/40 px-2.5 py-1 text-[10px] font-semibold text-green-400 hover:bg-green-500/10 transition-colors whitespace-nowrap"
                    >
                      Prep &rarr;
                    </button>
                  </div>
                  {/* Expanded memory card */}
                  {isExpanded && cards && (
                    <div className="px-3 pb-3 pt-1 border-t border-dark-700/30 mx-3">
                      <ul className="space-y-1 mb-2">
                        {cards.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-xs text-dark-300">
                            <ChevronRight className="h-3 w-3 text-dark-500 mt-0.5 flex-shrink-0" />
                            {item.text}
                          </li>
                        ))}
                      </ul>
                      <a
                        href={`/opponents/${slug(opp.name)}`}
                        className="text-xs text-forge-400 hover:text-forge-300 transition-colors"
                      >
                        View Full Dossier &rarr;
                      </a>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* BRACKET VIEWER */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5 xl:col-span-2">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <Target className="h-4 w-4 text-forge-400" /> Bracket Viewer
          </h2>
          <div className="flex gap-4 overflow-x-auto pb-2">
            {BRACKET_ROUNDS.map((round) => (
              <div key={round.round} className="flex-shrink-0 min-w-[160px]">
                <p className="text-xs font-bold text-dark-400 uppercase mb-2">{round.round}</p>
                <div className="space-y-2">
                  {round.matchups.map((match, mi) => (
                    <div key={mi} className="rounded-lg border border-dark-700/50 bg-dark-800/60 p-2">
                      {match.players.map((player, pi) => {
                        const isYou = player.startsWith('You');
                        const isTBD = player === 'TBD';
                        const cleanName = player.replace(/\s+\(W\)$/, '');
                        const tbdTitle = isTBD && match.sourceMatch
                          ? `Winner of ${match.sourceMatch}${match.expectedTime ? ` — game starts at ${match.expectedTime}` : ''}`
                          : isTBD
                          ? 'To be determined'
                          : undefined;
                        const baseClass = `px-2 py-1 text-xs rounded transition-colors ${
                          isYou ? 'bg-forge-500/15 text-forge-400 font-semibold' : 'text-dark-300'
                        } ${pi === 0 ? 'border-b border-dark-700/30 mb-1 pb-1' : ''}`;
                        if (isTBD) {
                          return (
                            <div key={pi} className={`${baseClass} text-dark-500 italic cursor-help`} title={tbdTitle}>
                              {player}
                            </div>
                          );
                        }
                        if (isYou) {
                          return (
                            <div key={pi} className={baseClass}>
                              {player}
                            </div>
                          );
                        }
                        return (
                          <button
                            key={pi}
                            type="button"
                            onClick={() => router.push(`/opponents/${slug(cleanName)}`)}
                            className={`${baseClass} block w-full text-left hover:text-forge-300`}
                          >
                            {player}
                          </button>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Task 2F: Bracket Intelligence */}
          <div className="mt-4 pt-3 border-t border-dark-700/50">
            <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
              <h3 className="flex items-center gap-2 text-xs font-semibold text-amber-300 mb-1">
                <AlertTriangle className="h-3.5 w-3.5" /> Bracket Intelligence
              </h3>
              {allWithinRange ? (
                <p className="text-xs text-dark-300">
                  No clear threat — all matchups within your win range.
                </p>
              ) : (
                <>
                  <p className="text-xs text-dark-300">
                    Hardest potential matchup: <span className="font-semibold text-dark-100">{hardestOpponent.name}</span>{' '}
                    ({hardestOpponent.archetype}). Your win rate vs {hardestOpponent.archetype}:{' '}
                    <button
                      type="button"
                      onClick={() => setShowBenchmark(true)}
                      className="font-semibold text-amber-300 underline-offset-2 hover:underline"
                    >
                      {hardestOpponent.winRate}%
                    </button>
                    . Likely encounter: Round 3 or later.
                  </p>
                  <button
                    type="button"
                    onClick={() => setShowCounterPackage(true)}
                    className="mt-2 rounded-lg border border-forge-500/30 bg-forge-500/10 px-3 py-1.5 text-xs font-semibold text-forge-400 hover:bg-forge-500/20 transition-colors"
                  >
                    View Counter Package &rarr;
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* WARMUP CHECKLIST — Task 2D */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <CheckSquare className="h-4 w-4 text-forge-400" /> Warmup Checklist
          </h2>
          <div className="space-y-3">
            {WARMUP_CHECKLIST_ITEMS.map((item) => (
              <label key={item.id} className="flex items-center gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={checklist[item.id] ?? false}
                  onChange={() => setChecklist((p) => ({ ...p, [item.id]: !p[item.id] }))}
                  className="h-4 w-4 rounded border-dark-600 bg-dark-800 text-forge-500 focus:ring-forge-500/30"
                />
                <span className={`text-sm ${checklist[item.id] ? 'text-dark-200 line-through' : 'text-dark-300'}`}>
                  {item.label}
                </span>
              </label>
            ))}
          </div>
          <div className="mt-4 pt-3 border-t border-dark-700/50 flex items-center justify-between">
            <p className="text-xs text-dark-400">
              {Object.values(checklist).filter(Boolean).length}/{WARMUP_CHECKLIST_ITEMS.length} complete
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowResetChecklistConfirm(true)}
                className="text-xs text-dark-500 hover:text-dark-300 transition-colors"
              >
                Reset Checklist
              </button>
              <button
                onClick={() => {
                  setChecklist(Object.fromEntries(WARMUP_CHECKLIST_ITEMS.map((i) => [i.id, true])));
                  setWarmupToast("Warmup complete — you're ready");
                  setTimeout(() => setWarmupToast(null), 3500);
                }}
                className="rounded-lg bg-forge-500/15 px-3 py-1.5 text-xs font-semibold text-forge-400 hover:bg-forge-500/25 transition-colors"
              >
                Complete All
              </button>
            </div>
          </div>
        </div>

        {/* BETWEEN-ROUND RESET — Task 2B */}
        <div ref={resetSectionRef} className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <Brain className="h-4 w-4 text-forge-400" /> Between-Round Reset
          </h2>
          <div className="space-y-3">
            {RESET_STEPS.map((s, idx) => (
              <div key={s.step} className="flex items-start gap-3">
                {idx === 0 ? (
                  /* Step 1: breathing timer */
                  <>
                    <button
                      onClick={() => setResetSteps((prev) => { const next = [...prev]; next[0] = !next[0]; return next; })}
                      className={`flex h-6 w-6 items-center justify-center rounded-full flex-shrink-0 transition-colors ${
                        resetSteps[0]
                          ? 'bg-forge-400 text-dark-900'
                          : 'bg-forge-500/15 text-forge-400'
                      }`}
                    >
                      {resetSteps[0] ? (
                        <span className="text-xs font-bold">&#10003;</span>
                      ) : (
                        <span className="text-xs font-bold">{s.step}</span>
                      )}
                    </button>
                    <div className="flex-1">
                      <p className={`text-sm ${resetSteps[0] ? 'text-dark-500 line-through' : 'text-dark-300'}`}>
                        {s.text}
                      </p>
                      {!resetSteps[0] && !breathingActive && (
                        <button
                          onClick={() => setBreathingActive(true)}
                          className="mt-1 rounded-md bg-forge-500/15 px-2 py-1 text-xs font-semibold text-forge-400 hover:bg-forge-500/25 transition-colors"
                        >
                          [30s] Start Breathing
                        </button>
                      )}
                      {breathingActive && (
                        <div className="mt-1 flex items-center gap-2">
                          <span className="text-xs font-mono text-forge-400">{breathTimer}s</span>
                          <span className="rounded-full bg-forge-500/15 px-2 py-0.5 text-xs font-semibold text-forge-400">
                            {breathPhase} 4...
                          </span>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  /* Steps 2-5: tappable checkboxes */
                  <>
                    <button
                      onClick={() => setResetSteps((prev) => { const next = [...prev]; next[idx] = !next[idx]; return next; })}
                      className={`flex h-6 w-6 items-center justify-center rounded-full flex-shrink-0 cursor-pointer transition-colors ${
                        resetSteps[idx]
                          ? 'bg-forge-400 text-dark-900'
                          : 'bg-forge-500/15 text-forge-400'
                      }`}
                    >
                      {resetSteps[idx] ? (
                        <span className="text-xs font-bold">&#10003;</span>
                      ) : (
                        <span className="text-xs font-bold">{s.step}</span>
                      )}
                    </button>
                    <p className={`text-sm ${resetSteps[idx] ? 'text-dark-500 line-through' : 'text-dark-300'}`}>
                      {s.text}
                    </p>
                  </>
                )}
              </div>
            ))}
          </div>
          <div className="mt-4 pt-3 border-t border-dark-700/50">
            <p className="text-xs text-dark-400 mb-2">{resetCount}/5 steps complete</p>
            <div className="flex items-center gap-3">
              {resetComplete && (
                <span className="rounded-lg bg-green-500/15 border border-green-500/30 px-3 py-1.5 text-xs font-semibold text-green-400">
                  Reset Complete &middot; routing to next round prep…
                </span>
              )}
              <button
                onClick={() => {
                  setResetSteps([false, false, false, false, false]);
                  setBreathingActive(false);
                  setBreathTimer(30);
                  setBreathPhase('Inhale');
                }}
                className="text-xs text-dark-500 hover:text-dark-300 transition-colors"
              >
                Start Over
              </button>
            </div>
          </div>
        </div>

        {/* MEMORY CARDS */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <Zap className="h-4 w-4 text-forge-400" /> Memory Cards
          </h2>
          <div className="space-y-3">
            {Object.entries(MEMORY_CARDS).map(([opponent, items]) => {
              const opp = OPPONENT_QUEUE.find((o) => o.name === opponent);
              const wr = opp?.winRate ?? 50;
              const borderClass = wr >= 60
                ? 'border border-green-500/30'
                : wr >= 40
                ? 'border border-amber-500/30'
                : 'border border-red-500/30';
              const merged = [...items, ...(customCards[opponent] ?? [])];
              return (
                <div key={opponent} className={`rounded-lg bg-dark-800/60 p-3 ${borderClass}`}>
                  <button
                    type="button"
                    onClick={() => router.push(`/opponents/${slug(opponent)}`)}
                    className="text-xs font-semibold text-forge-400 hover:text-forge-300 mb-1 transition-colors"
                  >
                    {opponent}
                  </button>
                  <ul className="space-y-1">
                    {merged.map((item, i) => (
                      <li key={i}>
                        <button
                          type="button"
                          onClick={() => setBulletDetail({ opponent, bullet: item })}
                          className="flex items-start gap-2 text-xs text-dark-300 hover:text-dark-100 transition-colors text-left w-full"
                        >
                          <ChevronRight className="h-3 w-3 text-dark-500 mt-0.5 flex-shrink-0" />
                          <span>{item.text}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
          <button
            type="button"
            onClick={() => setShowAddMemoryCard(true)}
            className="mt-3 flex items-center gap-1.5 rounded-lg border border-dashed border-dark-600 px-3 py-2 text-xs text-dark-400 hover:text-forge-300 hover:border-forge-500/40 w-full justify-center transition-colors"
          >
            <Plus className="h-3.5 w-3.5" /> Add Memory Card
          </button>
        </div>

        {/* FAST NOTE ENTRY */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <StickyNote className="h-4 w-4 text-forge-400" /> Fast Notes
          </h2>
          <div className="flex gap-2 mb-3">
            <textarea
              value={noteInput}
              onChange={(e) => setNoteInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); addNote(); } }}
              placeholder="Quick note..."
              className="flex-1 resize-none rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-100 placeholder-dark-500 focus:border-forge-500/50 focus:outline-none focus:ring-1 focus:ring-forge-500/30"
              rows={2}
            />
            <button
              onClick={addNote}
              className="rounded-lg bg-forge-500/15 px-3 text-xs font-semibold text-forge-400 hover:bg-forge-500/25 transition-colors"
            >
              Add
            </button>
          </div>
          <div className="space-y-1.5 max-h-32 overflow-y-auto">
            {notes.length === 0 && <p className="text-xs text-dark-500 italic">No notes yet</p>}
            {notes.map((n) => (
              <div key={n.id} className="group flex gap-2 text-xs items-start">
                <span className="text-dark-500 font-mono whitespace-nowrap">{n.time}</span>
                <span className="text-dark-300 flex-1">{n.text}</span>
                <button
                  type="button"
                  onClick={() => deleteNote(n.id)}
                  className="text-dark-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-label="Delete note"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* CURRENT GAMEPLAN — Task 2G + C10 */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5 xl:col-span-2">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <Gamepad2 className="h-4 w-4 text-forge-400" /> Active Gameplan (15 Plays)
          </h2>
          <div className="flex flex-wrap gap-1.5 mb-3">
            {([
              { id: 'all', label: 'All' },
              { id: 'cover3', label: 'vs Cover 3' },
              { id: 'redzone', label: 'Red Zone' },
              { id: '3rd', label: '3rd Down' },
              { id: '2min', label: '2-Min' },
            ] as const).map((f) => (
              <button
                key={f.id}
                type="button"
                onClick={() => setGameplanFilter(f.id)}
                className={`rounded-full px-3 py-1 text-[11px] font-semibold transition-colors ${
                  gameplanFilter === f.id
                    ? 'bg-forge-500/20 text-forge-300 border border-forge-500/40'
                    : 'bg-dark-800 text-dark-400 border border-dark-700 hover:border-forge-500/30 hover:text-forge-300'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {GAMEPLAN.filter((play) => {
              const blob = `${play.situation} ${play.note}`.toLowerCase();
              switch (gameplanFilter) {
                case 'cover3': return blob.includes('cover 3') || blob.includes('zone');
                case 'redzone': return blob.includes('red zone') || blob.includes('redzone');
                case '3rd': return blob.includes('3rd');
                case '2min': return blob.includes('2-min') || blob.includes('desperation');
                default: return true;
              }
            }).map((play) => (
              <button
                key={play.id}
                type="button"
                onClick={() => setPlayDetail(play)}
                className="flex items-center gap-2 rounded-lg bg-dark-800/60 px-3 py-2 hover:bg-dark-800 hover:ring-1 hover:ring-forge-500/30 transition-all text-left"
              >
                <span className="text-xs font-bold text-dark-500 w-5">{play.id}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-dark-100 truncate">{play.play}</p>
                  <p className="text-[10px] text-dark-500">{play.situation} — {play.note}</p>
                </div>
                <span
                  className="text-xs font-bold tabular-nums"
                  style={{ color: confidenceColor(play.confidence) }}
                >
                  {play.confidence}%
                </span>
              </button>
            ))}
          </div>
          <div className="mt-3 pt-3 border-t border-dark-700/50">
            <a
              href={`/gameplan?opponent=${slug(TOURNAMENT.nextOpponent)}&tab=killsheet`}
              className="text-xs text-forge-400 hover:text-forge-300 transition-colors"
            >
              View full kill sheet &rarr;
            </a>
          </div>
        </div>

        {/* CLOCK SECTION — 2-Minute Drill Decision Tree (C11) */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200">
              <Timer className="h-4 w-4 text-forge-400" /> 2-Minute Drill Tree
            </h2>
            <button
              type="button"
              onClick={() => {
                if (drillModeActive) {
                  setDrillModeActive(false);
                } else {
                  setDrillModeRemaining(120);
                  setDrillModeActive(true);
                }
              }}
              className={`flex items-center gap-1 rounded-lg px-2.5 py-1 text-[11px] font-semibold transition-colors ${
                drillModeActive
                  ? 'bg-red-500/15 border border-red-500/40 text-red-300'
                  : 'bg-forge-500/15 border border-forge-500/40 text-forge-300 hover:bg-forge-500/25'
              }`}
            >
              {drillModeActive ? (
                <><Pause className="h-3 w-3" /> {Math.floor(drillModeRemaining / 60)}:{(drillModeRemaining % 60).toString().padStart(2, '0')}</>
              ) : (
                <><Play className="h-3 w-3" /> Start 2-Min Drill Mode</>
              )}
            </button>
          </div>
          <div className="space-y-2">
            {CLOCK_TREE.map((node, idx) => {
              const isCurrent = idx === activeClockIndex;
              return (
                <button
                  key={node.time}
                  type="button"
                  onClick={() => setClockNodeDetail(node)}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 w-full text-left transition-colors ${
                    isCurrent
                      ? 'bg-forge-500/10 ring-2 ring-forge-500/50 animate-pulse'
                      : 'bg-dark-800/60 hover:bg-dark-800 hover:ring-1 hover:ring-forge-500/30'
                  }`}
                >
                  <span className="text-xs font-bold text-forge-400 font-mono w-10">{node.time}</span>
                  <div className="flex-1">
                    <p className="text-xs text-dark-400">{node.condition}</p>
                    <p className="text-xs font-medium text-dark-200">{node.action}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* SESSION HEALTH */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <Activity className="h-4 w-4 text-forge-400" /> Session Health
          </h2>
          <div className="space-y-4">
            {/* TiltGuard Status */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-dark-400">TiltGuard</span>
              <div className="flex items-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full ${
                  tiltStatus === 'green' ? 'bg-forge-400' : tiltStatus === 'yellow' ? 'bg-amber-400' : 'bg-red-400'
                }`} />
                <span className="text-xs font-medium text-dark-200 capitalize">{tiltStatus}</span>
              </div>
            </div>
            {/* Fatigue */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-dark-400">Fatigue</span>
                <span className="text-xs font-medium text-dark-200">{fatigue}%</span>
              </div>
              <div className="h-2 rounded-full bg-dark-800">
                <div
                  className="h-2 rounded-full bg-forge-400 transition-all"
                  style={{ width: `${fatigue}%` }}
                />
              </div>
            </div>
            {/* Break Timing */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-dark-400">Next break in</span>
              <span className="text-xs font-medium text-dark-200">{breakTimer} min</span>
            </div>
          </div>
        </div>

        {/* FAILSAFE MODE TOGGLE */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <ShieldOff className="h-4 w-4 text-forge-400" /> Failsafe Mode
          </h2>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-dark-200">Offline Mode</p>
              <p className="text-xs text-dark-400 mt-0.5">Disable network-dependent features</p>
            </div>
            <button
              onClick={() => setFailsafeMode(!failsafeMode)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                failsafeMode ? 'bg-forge-500' : 'bg-dark-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
                  failsafeMode ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          {failsafeMode && (
            <div className="mt-3 flex items-center gap-2 rounded-lg bg-amber-500/10 border border-amber-500/20 px-3 py-2">
              <AlertTriangle className="h-4 w-4 text-amber-400 flex-shrink-0" />
              <p className="text-xs text-amber-300">Failsafe active — using cached data only</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

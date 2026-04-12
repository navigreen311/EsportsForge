/**
 * TournaOps — Tournament Operations Console.
 * Real-time tournament management with bracket viewer, opponent queue,
 * warmup checklist, memory cards, session health, and fast note entry.
 */

'use client';

import { useState, useEffect } from 'react';
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
  AlertTriangle,
  Zap,
  Target,
} from 'lucide-react';

// --- Mock Data ---

const TOURNAMENT = {
  name: 'Friday Night Lights Championship',
  bracketPosition: 'Winners Round 3',
  record: '4-1',
  nextOpponent: 'xViper_Elite',
  nextMatchTime: new Date(Date.now() + 42 * 60 * 1000), // 42 min from now
  seed: 3,
  totalPlayers: 32,
};

const OPPONENT_QUEUE = [
  { name: 'xViper_Elite', archetype: 'Aggressive Rush', prep: 'ready', winRate: 62 },
  { name: 'ColdRead99', archetype: 'Zone Coverage', prep: 'partial', winRate: 55 },
  { name: 'BlitzKing_', archetype: 'Blitz Heavy', prep: 'ready', winRate: 48 },
  { name: 'SchemeMaster', archetype: 'West Coast', prep: 'none', winRate: 70 },
  { name: 'LabRat420', archetype: 'Spread Option', prep: 'partial', winRate: 58 },
];

const BRACKET_ROUNDS = [
  { round: 'R1', matchups: [['You (W)', 'Player16'], ['xViper_Elite (W)', 'Player15']] },
  { round: 'R2', matchups: [['You (W)', 'ColdRead99'], ['xViper_Elite (W)', 'BlitzKing_']] },
  { round: 'R3', matchups: [['You', 'xViper_Elite']] },
  { round: 'Final', matchups: [['TBD', 'TBD']] },
];

const WARMUP_CHECKLIST_ITEMS = [
  { id: 'schemes', label: 'Opponent schemes reviewed', default: true },
  { id: 'drills', label: 'Pre-match drills completed', default: true },
  { id: 'mental', label: 'Mental state check — focused', default: false },
  { id: 'killsheet', label: 'Kill sheet loaded', default: false },
];

const MEMORY_CARDS = [
  { opponent: 'xViper_Elite', items: ['Runs cover-3 on 1st down 80%', 'Blitzes on 3rd & long from nickel', 'Goes for it on 4th in opponent territory'] },
  { opponent: 'ColdRead99', items: ['Heavy zone, rarely man', 'Uses Tampa 2 shell in redzone', 'Audibles out of base on motion'] },
  { opponent: 'BlitzKing_', items: ['Fire zone on 2nd & long', 'Man coverage outside', 'Vulnerable to TE seam routes'] },
];

const GAMEPLAN = [
  { id: 1, play: 'Gun Trips TE — Mesh Spot', situation: '1st & 10', note: 'Beats Cover 3' },
  { id: 2, play: 'Singleback Ace — PA Crossers', situation: '2nd & Med', note: 'Cover 2 beater' },
  { id: 3, play: 'Shotgun Bunch — Corner Strike', situation: 'Red Zone', note: 'Man beater' },
  { id: 4, play: 'I-Form Close — HB Stretch', situation: '1st down', note: 'Run setup' },
  { id: 5, play: 'Gun Empty — 4 Verts', situation: '3rd & Long', note: 'Aggressive shot' },
  { id: 6, play: 'Pistol Strong — RPO Alert', situation: '2nd & Short', note: 'Read the LB' },
  { id: 7, play: 'Shotgun Spread — Slants', situation: '3rd & Med', note: 'Quick game' },
  { id: 8, play: 'Singleback Wing — Counter', situation: '1st & 10', note: 'Misdirection' },
  { id: 9, play: 'Gun Bunch — Levels Sail', situation: '2nd & Long', note: 'Zone flood' },
  { id: 10, play: 'Empty Trey — Stick Nod', situation: '3rd & Short', note: 'Easy conversion' },
  { id: 11, play: 'I-Form — PA Boot', situation: 'Opening script', note: 'Test deep' },
  { id: 12, play: 'Shotgun Trips — Screen', situation: 'Blitz response', note: 'Punish pressure' },
  { id: 13, play: 'Gun Doubles — Dagger', situation: 'Cover 2', note: 'Post-dig combo' },
  { id: 14, play: 'Singleback — Inside Zone', situation: 'Clock control', note: 'Safe yards' },
  { id: 15, play: 'Hail Mary / Scramble', situation: '2-min desperation', note: 'Last resort' },
];

const CLOCK_TREE = [
  { time: '2:00', condition: 'Down 3+', action: 'No huddle, attack sidelines' },
  { time: '1:30', condition: 'Need TD', action: 'Aggressive — 4 verts / crossers' },
  { time: '1:00', condition: 'In FG range', action: 'Run clock, kick at :05' },
  { time: '0:30', condition: 'Need TD still', action: 'Endzone shots only' },
  { time: '0:10', condition: 'Any', action: 'Spike or timeout, last play' },
];

export default function TournamentPage() {
  const [countdown, setCountdown] = useState('');
  const [checklist, setChecklist] = useState<Record<string, boolean>>(
    Object.fromEntries(WARMUP_CHECKLIST_ITEMS.map((i) => [i.id, i.default]))
  );
  const [notes, setNotes] = useState<{ time: string; text: string }[]>([]);
  const [noteInput, setNoteInput] = useState('');
  const [failsafeMode, setFailsafeMode] = useState(false);
  const [tiltStatus, setTiltStatus] = useState<'green' | 'yellow' | 'red'>('green');
  const [fatigue, setFatigue] = useState(28);
  const [breakTimer, setBreakTimer] = useState(12);

  // Countdown timer
  useEffect(() => {
    const interval = setInterval(() => {
      const diff = TOURNAMENT.nextMatchTime.getTime() - Date.now();
      if (diff <= 0) {
        setCountdown('LIVE NOW');
      } else {
        const m = Math.floor(diff / 60000);
        const s = Math.floor((diff % 60000) / 1000);
        setCountdown(`${m}:${s.toString().padStart(2, '0')}`);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const addNote = () => {
    if (!noteInput.trim()) return;
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setNotes((prev) => [{ time, text: noteInput.trim() }, ...prev]);
    setNoteInput('');
  };

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
              <h1 className="text-2xl font-bold text-dark-50">{TOURNAMENT.name}</h1>
              <p className="text-sm text-dark-400">
                {TOURNAMENT.bracketPosition} &middot; Record: {TOURNAMENT.record} &middot; Seed #{TOURNAMENT.seed}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <div className="rounded-lg bg-dark-800 px-4 py-2">
              <p className="text-xs text-dark-400">Next Opponent</p>
              <p className="text-sm font-semibold text-dark-50">{TOURNAMENT.nextOpponent}</p>
            </div>
            <div className="rounded-lg bg-forge-500/10 px-4 py-2 border border-forge-500/20">
              <p className="text-xs text-forge-400">Countdown</p>
              <p className="text-lg font-bold text-forge-400 font-mono">{countdown || '--:--'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* MAIN GRID */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 xl:grid-cols-3">

        {/* OPPONENT QUEUE */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <Users className="h-4 w-4 text-forge-400" /> Opponent Queue
          </h2>
          <div className="space-y-2">
            {OPPONENT_QUEUE.map((opp, i) => (
              <div key={opp.name} className="flex items-center gap-3 rounded-lg bg-dark-800/60 px-3 py-2">
                <span className="text-xs font-bold text-dark-500 w-5">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-dark-100 truncate">{opp.name}</p>
                  <p className="text-xs text-dark-400">{opp.archetype}</p>
                </div>
                <span className="text-xs text-dark-400">{opp.winRate}%</span>
                <span className={`h-2 w-2 rounded-full ${
                  opp.prep === 'ready' ? 'bg-forge-400' : opp.prep === 'partial' ? 'bg-amber-400' : 'bg-red-400'
                }`} title={`Prep: ${opp.prep}`} />
              </div>
            ))}
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
                      {match.map((player, pi) => (
                        <div
                          key={pi}
                          className={`px-2 py-1 text-xs rounded ${
                            player.startsWith('You')
                              ? 'bg-forge-500/15 text-forge-400 font-semibold'
                              : 'text-dark-300'
                          } ${pi === 0 ? 'border-b border-dark-700/30 mb-1 pb-1' : ''}`}
                        >
                          {player}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* WARMUP CHECKLIST */}
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
          <div className="mt-4 pt-3 border-t border-dark-700/50">
            <p className="text-xs text-dark-400">
              {Object.values(checklist).filter(Boolean).length}/{WARMUP_CHECKLIST_ITEMS.length} complete
            </p>
          </div>
        </div>

        {/* BETWEEN-ROUND RESET */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <Brain className="h-4 w-4 text-forge-400" /> Between-Round Reset
          </h2>
          <div className="space-y-3">
            {[
              { step: 1, text: 'Close eyes, 4 deep breaths (box breathing)' },
              { step: 2, text: 'Name 1 thing you did well last game' },
              { step: 3, text: 'Identify 1 adjustment for next game' },
              { step: 4, text: 'Visualize your opening script executing' },
              { step: 5, text: 'Reset posture — shoulders back, hands loose' },
            ].map((s) => (
              <div key={s.step} className="flex items-start gap-3">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-forge-500/15 text-xs font-bold text-forge-400 flex-shrink-0">
                  {s.step}
                </span>
                <p className="text-sm text-dark-300">{s.text}</p>
              </div>
            ))}
          </div>
        </div>

        {/* MEMORY CARDS */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <Zap className="h-4 w-4 text-forge-400" /> Memory Cards
          </h2>
          <div className="space-y-3">
            {MEMORY_CARDS.map((card) => (
              <div key={card.opponent} className="rounded-lg bg-dark-800/60 p-3">
                <p className="text-xs font-semibold text-forge-400 mb-1">{card.opponent}</p>
                <ul className="space-y-1">
                  {card.items.map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-dark-300">
                      <ChevronRight className="h-3 w-3 text-dark-500 mt-0.5 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
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
            {notes.map((n, i) => (
              <div key={i} className="flex gap-2 text-xs">
                <span className="text-dark-500 font-mono whitespace-nowrap">{n.time}</span>
                <span className="text-dark-300">{n.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* CURRENT GAMEPLAN */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5 xl:col-span-2">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <Gamepad2 className="h-4 w-4 text-forge-400" /> Active Gameplan (15 Plays)
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {GAMEPLAN.map((play) => (
              <div key={play.id} className="flex items-center gap-2 rounded-lg bg-dark-800/60 px-3 py-2">
                <span className="text-xs font-bold text-dark-500 w-5">{play.id}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-dark-100 truncate">{play.play}</p>
                  <p className="text-[10px] text-dark-500">{play.situation} — {play.note}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-3 pt-3 border-t border-dark-700/50">
            <a href="/gameplan" className="text-xs text-forge-400 hover:text-forge-300 transition-colors">
              View full kill sheet &rarr;
            </a>
          </div>
        </div>

        {/* CLOCK SECTION — 2-Minute Drill Decision Tree */}
        <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
            <Timer className="h-4 w-4 text-forge-400" /> 2-Minute Drill Tree
          </h2>
          <div className="space-y-2">
            {CLOCK_TREE.map((node) => (
              <div key={node.time} className="flex items-center gap-3 rounded-lg bg-dark-800/60 px-3 py-2">
                <span className="text-xs font-bold text-forge-400 font-mono w-10">{node.time}</span>
                <div className="flex-1">
                  <p className="text-xs text-dark-400">{node.condition}</p>
                  <p className="text-xs font-medium text-dark-200">{node.action}</p>
                </div>
              </div>
            ))}
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

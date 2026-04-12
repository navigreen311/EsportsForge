/**
 * SimLab — Scenario Sandbox.
 * Pre-built and custom scenario simulations with decision trees,
 * rep tracking, and results analysis.
 */

'use client';

import { useState } from 'react';
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
} from 'lucide-react';

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
}

export default function SimLabPage() {
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [selectedOpponent, setSelectedOpponent] = useState(MOCK_OPPONENTS[0]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [showResult, setShowResult] = useState(false);
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

  const runSimulation = () => {
    setIsSimulating(true);
    setShowResult(false);
    setTimeout(() => {
      setIsSimulating(false);
      setShowResult(true);
      const correct = Math.random() > 0.35;
      const timeMs = 1500 + Math.random() * 3000;
      setReps((prev) => [
        {
          id: prev.length + 1,
          correct,
          timeMs: Math.round(timeMs),
          scenario: selectedScenario?.name ?? 'Custom',
        },
        ...prev,
      ]);
    }, 1500);
  };

  const accuracy = reps.length > 0
    ? Math.round((reps.filter((r) => r.correct).length / reps.length) * 100)
    : 0;
  const avgTime = reps.length > 0
    ? Math.round(reps.reduce((a, r) => a + r.timeMs, 0) / reps.length)
    : 0;

  return (
    <div className="space-y-6">
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
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-dark-800 px-3 py-1.5 text-xs text-dark-300">
            <span className="text-dark-500">Reps today:</span> <span className="font-semibold text-dark-100">{reps.length}</span>
          </div>
          <div className="rounded-lg bg-dark-800 px-3 py-1.5 text-xs text-dark-300">
            <span className="text-dark-500">Accuracy:</span> <span className="font-semibold text-forge-400">{accuracy}%</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* LEFT COLUMN — Scenario Selector + Custom Builder */}
        <div className="space-y-6">
          {/* SCENARIO SELECTOR */}
          <div className="rounded-xl border border-dark-700/50 bg-dark-900 p-5">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-dark-200 mb-4">
              <Target className="h-4 w-4 text-forge-400" /> Scenarios
            </h2>
            <div className="grid grid-cols-2 gap-2">
              {SCENARIOS.map((s) => (
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

            {/* Run Button */}
            <button
              onClick={runSimulation}
              disabled={isSimulating}
              className="w-full rounded-lg bg-forge-500 py-2.5 text-sm font-semibold text-dark-950 hover:bg-forge-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSimulating ? 'Simulating...' : 'Run Scenario'}
            </button>

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
              {reps.map((rep) => (
                <div key={rep.id} className="flex items-center gap-3 rounded-lg bg-dark-800/60 px-3 py-2">
                  {rep.correct ? (
                    <CheckCircle2 className="h-4 w-4 text-forge-400 flex-shrink-0" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-dark-200 truncate">{rep.scenario}</p>
                    <p className="text-[10px] text-dark-500">Rep #{rep.id}</p>
                  </div>
                  <span className="text-xs font-mono text-dark-400">
                    {(rep.timeMs / 1000).toFixed(1)}s
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

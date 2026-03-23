'use client';

import { useState } from 'react';
import { Brain } from 'lucide-react';

/* ─── Mock Data ─────────────────────────────────────────────── */

const favoriteConcepts = [
  { name: 'PA Crossers', confidence: 91 },
  { name: 'Mesh Concept', confidence: 84 },
  { name: 'Inside Zone', confidence: 78 },
];

const coverageRecognition = [
  { name: 'Cover 2', confidence: 88 },
  { name: 'Cover 3', confidence: 74 },
  { name: 'Man', confidence: 91 },
  { name: 'Cover 4', confidence: 52 },
];

const detectedTendencies = [
  'You prefer Cover 2 defense',
  'You tend to run on 1st down',
  'You avoid deep shots when trailing',
  'You blitz more in 4th quarter',
  'You favor right-side runs',
];

/* ─── Component ─────────────────────────────────────────────── */

export default function PlayerTwinSettings() {
  const [wrongFlags, setWrongFlags] = useState<Set<number>>(new Set());
  const [correctFlags, setCorrectFlags] = useState<Set<number>>(new Set());
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const handleCorrect = (idx: number) => {
    setCorrectFlags((prev) => {
      const next = new Set(prev);
      next.add(idx);
      next.delete(idx); // toggle off wrong if set
      return next;
    });
    // Remove from correct set to re-add properly
    setCorrectFlags((prev) => new Set([...prev, idx]));
    setWrongFlags((prev) => {
      const next = new Set(prev);
      next.delete(idx);
      return next;
    });
  };

  const handleWrong = (idx: number) => {
    setWrongFlags((prev) => new Set([...prev, idx]));
    setCorrectFlags((prev) => {
      const next = new Set(prev);
      next.delete(idx);
      return next;
    });
  };

  const twinAccuracy = 78;
  const gamesUsed = 42;

  return (
    <div className="space-y-6">
      {/* ── Section A: Your Twin Profile ── */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-5 h-5 text-forge-400" />
          <h3 className="text-sm font-bold text-dark-100 uppercase tracking-wider">
            Your Twin Profile
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Favorite Concepts */}
          <div className="rounded-lg border border-dark-700 bg-dark-800/50 p-4">
            <p className="text-xs text-dark-500 uppercase tracking-wider mb-2">
              Favorite Concepts
            </p>
            <ol className="space-y-1.5">
              {favoriteConcepts.map((c, i) => (
                <li
                  key={c.name}
                  className={`flex items-center justify-between text-sm ${
                    c.confidence < 60 ? 'opacity-50 italic' : ''
                  }`}
                >
                  <span className="text-dark-200">
                    {i + 1}. {c.name}
                  </span>
                  <span className="text-xs text-forge-400 font-medium">
                    {c.confidence}% conf
                  </span>
                </li>
              ))}
            </ol>
          </div>

          {/* Panic Pattern */}
          <div className="rounded-lg border border-dark-700 bg-dark-800/50 p-4">
            <p className="text-xs text-dark-500 uppercase tracking-wider mb-2">
              Panic Pattern
            </p>
            <p className="text-sm text-dark-200">
              Holds ball too long under pressure (0.4s above baseline)
            </p>
            <p className="text-xs text-dark-400 mt-1">72% confidence</p>
          </div>

          {/* Execution Ceiling */}
          <div className="rounded-lg border border-dark-700 bg-dark-800/50 p-4">
            <p className="text-xs text-dark-500 uppercase tracking-wider mb-2">
              Execution Ceiling
            </p>
            <div className="flex items-center gap-4">
              <div>
                <p className="text-sm text-dark-200">Normal</p>
                <p className="text-lg font-bold text-forge-400">82%</p>
              </div>
              <div className="h-8 w-px bg-dark-700" />
              <div>
                <p className="text-sm text-dark-200">Under Pressure</p>
                <p className="text-lg font-bold text-red-400">61%</p>
              </div>
            </div>
          </div>

          {/* Coverage Recognition */}
          <div className="rounded-lg border border-dark-700 bg-dark-800/50 p-4">
            <p className="text-xs text-dark-500 uppercase tracking-wider mb-2">
              Coverage Recognition
            </p>
            <div className="flex flex-wrap gap-3">
              {coverageRecognition.map((c) => (
                <div
                  key={c.name}
                  className={`text-sm ${
                    c.confidence < 60 ? 'opacity-50 italic' : ''
                  }`}
                >
                  <span className="text-dark-200">{c.name}:</span>{' '}
                  <span
                    className={`font-medium ${
                      c.confidence < 60 ? 'text-dark-500' : 'text-forge-400'
                    }`}
                  >
                    {c.confidence}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Section B: Twin Accuracy ── */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h3 className="text-sm font-bold text-dark-100 uppercase tracking-wider mb-4">
          Twin Accuracy
        </h3>

        <div className="flex items-center gap-6">
          {/* Circular-style accuracy indicator */}
          <div className="relative flex items-center justify-center w-28 h-28 shrink-0">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="42"
                fill="none"
                stroke="currentColor"
                strokeWidth="8"
                className="text-dark-700"
              />
              <circle
                cx="50"
                cy="50"
                r="42"
                fill="none"
                stroke="currentColor"
                strokeWidth="8"
                strokeDasharray={`${twinAccuracy * 2.64} ${264}`}
                strokeLinecap="round"
                className="text-forge-500"
              />
            </svg>
            <span className="absolute text-2xl font-bold text-dark-50">
              {twinAccuracy}%
            </span>
          </div>

          <div className="space-y-1.5">
            <p className="text-sm text-dark-200">
              <span className="font-medium text-dark-100">{gamesUsed}</span>{' '}
              games used to train twin
            </p>
            <p className="text-xs text-dark-400">
              Last updated: 2 hours ago — after game vs.{' '}
              <span className="text-dark-300">xXDragonSlayerXx</span>
            </p>
          </div>
        </div>
      </div>

      {/* ── Section C: Manual Corrections ── */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h3 className="text-sm font-bold text-dark-100 uppercase tracking-wider mb-4">
          Manual Corrections
        </h3>

        <div className="space-y-3">
          {detectedTendencies.map((tendency, idx) => {
            const isWrong = wrongFlags.has(idx);
            const isCorrect = correctFlags.has(idx);

            return (
              <div
                key={idx}
                className="flex items-center justify-between gap-3 rounded-lg border border-dark-700 bg-dark-800/50 px-4 py-3"
              >
                <div className="flex-1 min-w-0">
                  <p
                    className={`text-sm ${
                      isWrong
                        ? 'line-through text-dark-500'
                        : 'text-dark-200'
                    }`}
                  >
                    {tendency}
                  </p>
                  {isWrong && (
                    <p className="text-xs text-red-400 mt-0.5">
                      Flagged for LoopAI review
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleCorrect(idx)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                      isCorrect
                        ? 'bg-forge-600 text-white'
                        : 'bg-forge-500/10 text-forge-400 hover:bg-forge-500/20'
                    }`}
                  >
                    Correct
                  </button>
                  <button
                    onClick={() => handleWrong(idx)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                      isWrong
                        ? 'bg-red-600 text-white'
                        : 'bg-red-500/10 text-red-400 hover:bg-red-500/20'
                    }`}
                  >
                    Wrong
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Section D: Twin Controls ── */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h3 className="text-sm font-bold text-dark-100 uppercase tracking-wider mb-4">
          Twin Controls
        </h3>

        <div className="flex flex-wrap gap-3">
          <button className="rounded-lg bg-forge-500 px-5 py-2.5 text-sm font-medium text-white hover:bg-forge-400 transition-colors">
            Recalibrate Twin
          </button>

          {!showResetConfirm ? (
            <button
              onClick={() => setShowResetConfirm(true)}
              className="rounded-lg bg-red-500/20 px-5 py-2.5 text-sm font-medium text-red-400 hover:bg-red-500/30 transition-colors"
            >
              Reset Twin
            </button>
          ) : (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2.5">
              <p className="text-xs text-red-300 mr-2">
                This will erase all twin data. Are you sure?
              </p>
              <button
                onClick={() => setShowResetConfirm(false)}
                className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-500 transition-colors"
              >
                Confirm Reset
              </button>
              <button
                onClick={() => setShowResetConfirm(false)}
                className="rounded-lg bg-dark-700 px-3 py-1.5 text-xs font-medium text-dark-300 hover:bg-dark-600 transition-colors"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

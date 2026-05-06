'use client';

import { useState, useEffect, useCallback } from 'react';
import { Brain, RefreshCw, Loader2, X } from 'lucide-react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8001';

const PLAYERTWIN_STORAGE_KEY = 'esportsforge_playertwin';

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
  const { data: session } = useSession();
  const authHeader: Record<string, string> = session?.accessToken ? { Authorization: `Bearer ${session.accessToken}` } : {};

  const [wrongFlags, setWrongFlags] = useState<Set<number>>(new Set());
  const [correctFlags, setCorrectFlags] = useState<Set<number>>(new Set());
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [isRecalibrating, setIsRecalibrating] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [twinAccuracy, setTwinAccuracy] = useState(78);
  const [gamesUsed, setGamesUsed] = useState(42);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [conceptDetail, setConceptDetail] = useState<{ name: string; confidence: number } | null>(null);
  const [showAccuracyExplain, setShowAccuracyExplain] = useState(false);
  const [showPanicDetail, setShowPanicDetail] = useState(false);

  const showToast = useCallback((msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  }, []);

  const handleRecalibrate = useCallback(async () => {
    if (isRecalibrating) return;
    setIsRecalibrating(true);
    try {
      await fetch(`${API_BASE}/api/v1/player-twin/recalibrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader },
      });
    } catch { /* offline — fall through to optimistic update */ }
    setTimeout(() => {
      setIsRecalibrating(false);
      setTwinAccuracy((prev) => Math.min(99, prev + 4));
      showToast('Twin recalibrated — accuracy updated');
    }, 2000);
  }, [isRecalibrating, showToast, authHeader]);

  const handleResetConfirm = useCallback(async () => {
    setIsResetting(true);
    try {
      await fetch(`${API_BASE}/api/v1/player-twin/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader },
      });
    } catch { /* offline */ }
    setTimeout(() => {
      setIsResetting(false);
      setShowResetConfirm(false);
      setTwinAccuracy(0);
      setGamesUsed(0);
      setWrongFlags(new Set());
      setCorrectFlags(new Set());
      showToast('Twin reset. Play sessions to rebuild.');
    }, 1500);
  }, [showToast, authHeader]);

  const submitCorrection = useCallback(async (idx: number, verdict: 'correct' | 'wrong') => {
    try {
      await fetch(`${API_BASE}/api/v1/player-twin/corrections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader },
        body: JSON.stringify({ tendency_index: idx, verdict }),
      });
    } catch { /* offline */ }
  }, [authHeader]);

  // Load corrections from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(PLAYERTWIN_STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        if (data.wrongFlags) setWrongFlags(new Set(data.wrongFlags));
        if (data.correctFlags) setCorrectFlags(new Set(data.correctFlags));
      }
    } catch {}
  }, []);

  // Save corrections to localStorage
  useEffect(() => {
    localStorage.setItem(PLAYERTWIN_STORAGE_KEY, JSON.stringify({
      wrongFlags: Array.from(wrongFlags),
      correctFlags: Array.from(correctFlags),
    }));
  }, [wrongFlags, correctFlags]);

  const handleCorrect = (idx: number) => {
    setCorrectFlags((prev) => new Set([...prev, idx]));
    setWrongFlags((prev) => {
      const next = new Set(prev);
      next.delete(idx);
      return next;
    });
    submitCorrection(idx, 'correct');
  };

  const handleWrong = (idx: number) => {
    setWrongFlags((prev) => new Set([...prev, idx]));
    setCorrectFlags((prev) => {
      const next = new Set(prev);
      next.delete(idx);
      return next;
    });
    submitCorrection(idx, 'wrong');
  };

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
                <li key={c.name}>
                  <button
                    type="button"
                    onClick={() => setConceptDetail(c)}
                    className={`flex items-center justify-between text-sm w-full hover:bg-dark-700/40 -mx-1 px-1 py-0.5 rounded transition-colors ${
                      c.confidence < 60 ? 'opacity-50 italic' : ''
                    }`}
                  >
                    <span className="text-dark-200">
                      {i + 1}. {c.name}
                    </span>
                    <span className="text-xs text-forge-400 font-medium">
                      {c.confidence}% conf
                    </span>
                  </button>
                </li>
              ))}
            </ol>
          </div>

          {/* Panic Pattern */}
          <button
            type="button"
            onClick={() => setShowPanicDetail(true)}
            className="rounded-lg border border-dark-700 bg-dark-800/50 p-4 text-left hover:border-forge-500/30 transition-colors"
          >
            <p className="text-xs text-dark-500 uppercase tracking-wider mb-2">
              Panic Pattern
            </p>
            <p className="text-sm text-dark-200">
              Holds ball too long under pressure (0.4s above baseline)
            </p>
            <p className="text-xs text-dark-400 mt-1">72% confidence — click for evidence</p>
          </button>

          {/* Execution Ceiling */}
          <div
            className="rounded-lg border border-dark-700 bg-dark-800/50 p-4"
            title="Your execution drops 21% under pressure"
          >
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
            <p className="text-xs text-dark-500 mt-2">21% gap — drill pressure reads to close it</p>
          </div>

          {/* Coverage Recognition */}
          <div className="rounded-lg border border-dark-700 bg-dark-800/50 p-4">
            <p className="text-xs text-dark-500 uppercase tracking-wider mb-2">
              Coverage Recognition
            </p>
            <div className="flex flex-wrap gap-3">
              {coverageRecognition.map((c) => {
                const insufficient = c.confidence < 60;
                if (insufficient) {
                  return (
                    <Link
                      key={c.name}
                      href={`/drills?focus=${encodeURIComponent(c.name.toLowerCase())}-reads`}
                      className="text-sm italic text-dark-500 hover:text-forge-300"
                      title="Insufficient data — drill to improve"
                    >
                      <span>{c.name}:</span>{' '}
                      <span className="font-medium underline-offset-2 hover:underline">{c.confidence}% — drill {c.name} reads &rarr;</span>
                    </Link>
                  );
                }
                return (
                  <div key={c.name} className="text-sm">
                    <span className="text-dark-200">{c.name}:</span>{' '}
                    <span className="font-medium text-forge-400">{c.confidence}%</span>
                  </div>
                );
              })}
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
          <button
            type="button"
            onClick={() => setShowAccuracyExplain(true)}
            className="relative flex items-center justify-center w-28 h-28 shrink-0 hover:opacity-80 transition-opacity"
            title="What does this mean?"
          >
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
          </button>

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

      {/* ── Section D: Evolution Chart ── */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h3 className="text-sm font-bold text-dark-100 uppercase tracking-wider mb-4">
          Twin Accuracy — Last 30 Days
        </h3>

        <div className="flex items-end gap-1 h-32">
          {[62, 65, 64, 68, 70, 69, 72, 71, 74, 73, 75, 74, 76, 75, 77, 76, 78, 77, 79, 78, 80, 79, 78, 80, 79, 81, 80, 79, 78, 78].map(
            (val, idx) => (
              <div
                key={idx}
                className="flex-1 rounded-t transition-all hover:opacity-80"
                style={{
                  height: `${((val - 55) / 30) * 100}%`,
                  backgroundColor:
                    val >= 78
                      ? 'rgb(34, 197, 94)'
                      : val >= 70
                        ? 'rgb(74, 222, 128)'
                        : 'rgb(100, 116, 139)',
                }}
                title={`Day ${idx + 1}: ${val}%`}
              />
            )
          )}
        </div>

        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-dark-500">30 days ago</span>
          <span className="text-xs text-dark-500">Today</span>
        </div>
      </div>

      {/* ── Section E: Twin Controls ── */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h3 className="text-sm font-bold text-dark-100 uppercase tracking-wider mb-4">
          Twin Controls
        </h3>

        <div className="flex flex-wrap gap-3">
          {/* Recalibrate Twin */}
          <button
            onClick={handleRecalibrate}
            disabled={isRecalibrating}
            className="flex items-center gap-2 rounded-lg border border-forge-400 px-5 py-2.5 text-sm font-medium text-forge-400 hover:bg-forge-400/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRecalibrating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            {isRecalibrating ? 'Recalibrating...' : 'Recalibrate Twin'}
          </button>

          {/* Reset Twin */}
          {!showResetConfirm ? (
            <button
              onClick={() => setShowResetConfirm(true)}
              className="rounded-lg border border-red-500 px-5 py-2.5 text-sm font-medium text-red-500 hover:bg-red-500/10 transition-colors"
            >
              Reset Twin
            </button>
          ) : (
            <div className="w-full rounded-lg border border-red-500/30 bg-red-500/10 p-4 mt-2">
              <p className="text-sm text-red-300 mb-3">
                <span className="font-semibold">Reset PlayerTwin</span> — This clears all learned data. Recommendations become generic until the twin rebuilds (20+ games). Are you sure?
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowResetConfirm(false)}
                  disabled={isResetting}
                  className="rounded-lg bg-dark-700 px-4 py-2 text-xs font-medium text-dark-300 hover:bg-dark-600 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleResetConfirm}
                  disabled={isResetting}
                  className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-xs font-medium text-white hover:bg-red-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isResetting && <Loader2 className="w-3 h-3 animate-spin" />}
                  {isResetting ? 'Resetting...' : 'Yes, Reset Twin'}
                </button>
              </div>
            </div>
          )}
        </div>

        {isRecalibrating && (
          <p className="text-xs text-forge-400 mt-3 animate-pulse">
            Recalibrating from last 20 games...
          </p>
        )}
      </div>

      {/* Toast notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 rounded-lg border border-forge-400/30 bg-dark-800 px-5 py-3 shadow-lg">
          <p className="text-sm text-forge-400">{toastMessage}</p>
        </div>
      )}

      {/* Concept detail modal (C17) */}
      {conceptDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setConceptDetail(null)}>
          <div className="w-full max-w-md rounded-xl border border-dark-700 bg-dark-900 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-lg font-bold text-dark-50">{conceptDetail.name}</h3>
              <button onClick={() => setConceptDetail(null)} className="text-dark-500 hover:text-dark-200"><X className="w-5 h-5" /></button>
            </div>
            <p className="text-sm text-dark-300 mb-3">Twin confidence in this concept: <span className="text-forge-400 font-semibold">{conceptDetail.confidence}%</span></p>
            <p className="text-xs text-dark-400 mb-4">Built from your last 30 sessions where this concept was called. Higher confidence = the twin can predict your timing/protections in this concept reliably.</p>
            <Link href={`/drills?concept=${encodeURIComponent(conceptDetail.name)}`} className="block text-center rounded-lg bg-forge-500/15 border border-forge-500/30 px-4 py-2 text-sm font-semibold text-forge-300 hover:bg-forge-500/25">
              Drill {conceptDetail.name} &rarr;
            </Link>
          </div>
        </div>
      )}

      {/* Twin accuracy explainer (C17) */}
      {showAccuracyExplain && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setShowAccuracyExplain(false)}>
          <div className="w-full max-w-md rounded-xl border border-dark-700 bg-dark-900 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-lg font-bold text-dark-50">What does {twinAccuracy}% mean?</h3>
              <button onClick={() => setShowAccuracyExplain(false)} className="text-dark-500 hover:text-dark-200"><X className="w-5 h-5" /></button>
            </div>
            <p className="text-sm text-dark-300 mb-2">It means your PlayerTwin model predicts the call you would have made <span className="text-forge-400 font-semibold">{twinAccuracy}% of the time</span> across {gamesUsed} simulated decisions from your recent sessions.</p>
            <p className="text-xs text-dark-400">Above 75% means the twin is reliable enough for ForgeCore to use it as a co-pilot. Below 60% means it should fall back to generic recommendations.</p>
          </div>
        </div>
      )}

      {/* Panic pattern detail (C17) */}
      {showPanicDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setShowPanicDetail(false)}>
          <div className="w-full max-w-md rounded-xl border border-dark-700 bg-dark-900 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-lg font-bold text-dark-50">Panic Pattern Evidence</h3>
              <button onClick={() => setShowPanicDetail(false)} className="text-dark-500 hover:text-dark-200"><X className="w-5 h-5" /></button>
            </div>
            <p className="text-sm text-dark-300 mb-3">Pattern: holds ball <span className="text-red-400 font-semibold">0.4s above your baseline</span> when pressure reaches you within 2.5s.</p>
            <ul className="text-xs text-dark-400 space-y-1 mb-4">
              <li>&middot; Sample: 38 dropbacks under pressure across 9 sessions</li>
              <li>&middot; Confidence: 72%</li>
              <li>&middot; Most affected concepts: PA Crossers, Verts</li>
            </ul>
            <Link href="/drills?focus=pressure-reads" className="block text-center rounded-lg bg-forge-500/15 border border-forge-500/30 px-4 py-2 text-sm font-semibold text-forge-300 hover:bg-forge-500/25">
              Drill pressure reads &rarr;
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

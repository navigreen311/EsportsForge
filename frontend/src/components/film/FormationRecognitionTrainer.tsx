'use client';

import { useState } from 'react';
import { Eye, Check, X, Upload } from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Mock formation data — cycles through 5 defensive looks             */
/* ------------------------------------------------------------------ */

interface Formation {
  name: string;
  confidence: number;
  blitz: string;
  personnel: string;
}

const FORMATIONS: Formation[] = [
  { name: 'Cover 3 Shell', confidence: 94, blitz: 'None detected', personnel: 'Nickel (5 DBs)' },
  { name: 'Cover 2', confidence: 88, blitz: 'None detected', personnel: 'Base 4-3' },
  { name: 'Man Coverage', confidence: 91, blitz: 'OLB walk-up detected', personnel: 'Dime (6 DBs)' },
  { name: 'Cover 4', confidence: 76, blitz: 'None detected', personnel: 'Nickel (5 DBs)' },
  { name: 'Cover 0 Blitz', confidence: 82, blitz: 'OLB walk-up detected', personnel: 'Base 3-4' },
];

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function FormationRecognitionTrainer() {
  const [formationIdx, setFormationIdx] = useState(0);
  const [phase, setPhase] = useState<'upload' | 'processing' | 'result'>('upload');
  const [response, setResponse] = useState<'correct' | 'wrong' | null>(null);
  const [correct, setCorrect] = useState(7);
  const [total, setTotal] = useState(10);

  const formation = FORMATIONS[formationIdx];
  const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0;
  const progressPct = total > 0 ? Math.round((correct / total) * 100) : 0;

  /* ---------- handlers ---------- */

  function handleUpload() {
    setPhase('processing');
    setResponse(null);
    setTimeout(() => setPhase('result'), 1500);
  }

  function handleResponse(isCorrect: boolean) {
    setResponse(isCorrect ? 'correct' : 'wrong');
    setTotal((t) => t + 1);
    if (isCorrect) setCorrect((c) => c + 1);
  }

  function handleNext() {
    setFormationIdx((i) => (i + 1) % FORMATIONS.length);
    setPhase('upload');
    setResponse(null);
  }

  /* ---------- render ---------- */

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <Eye className="w-5 h-5 text-forge-400" />
          <h2 className="text-xl font-bold text-dark-50">Formation Recognition Trainer</h2>
        </div>
        <span className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider rounded-full bg-amber-500/15 text-amber-400 border border-amber-700/30">
          Offline Lab only — anti-cheat safe
        </span>
      </div>

      {/* Upload Zone */}
      {phase === 'upload' && (
        <button
          onClick={handleUpload}
          className="w-full flex flex-col items-center justify-center gap-3 py-12 rounded-lg border-2 border-dashed border-dark-600 hover:border-forge-500/50 bg-dark-800/40 hover:bg-dark-800/70 transition-colors cursor-pointer"
        >
          <Upload className="w-8 h-8 text-dark-400" />
          <span className="text-sm text-dark-300">Upload or capture a defensive formation screenshot</span>
        </button>
      )}

      {/* Processing */}
      {phase === 'processing' && (
        <div className="flex flex-col items-center justify-center py-14 gap-3">
          <div className="w-8 h-8 border-2 border-forge-400 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-dark-400">Analyzing formation...</span>
        </div>
      )}

      {/* Result */}
      {phase === 'result' && (
        <div className="space-y-4">
          {/* Detection badge */}
          <div className="p-4 rounded-lg bg-dark-800/60 border border-dark-700 space-y-2">
            <div className="flex items-center gap-3">
              <span className="px-3 py-1.5 text-lg font-bold rounded-lg bg-forge-500/20 text-forge-300 border border-forge-600/30">
                {formation.name} — {formation.confidence}% confidence
              </span>
            </div>
            <p className="text-sm text-dark-300">
              Detected: <span className="font-semibold text-dark-100">{formation.name}</span> — {formation.confidence}% confidence
            </p>
            <p className="text-sm text-dark-400">
              Blitz indicators:{' '}
              <span className={formation.blitz === 'None detected' ? 'text-dark-400' : 'text-amber-400 font-medium'}>
                {formation.blitz === 'None detected' ? 'None detected' : `Blitz: ${formation.blitz}`}
              </span>
            </p>
            <p className="text-sm text-dark-400">
              Personnel: <span className="text-dark-200 font-medium">{formation.personnel}</span>
            </p>
          </div>

          {/* Player response buttons */}
          {response === null && (
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleResponse(true)}
                className="flex items-center gap-2 px-5 py-2.5 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg transition-colors"
              >
                <Check className="w-4 h-4" />
                Correct
              </button>
              <button
                onClick={() => handleResponse(false)}
                className="flex items-center gap-2 px-5 py-2.5 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
                Wrong
              </button>
            </div>
          )}

          {/* Feedback */}
          {response === 'correct' && (
            <div className="p-3 rounded-lg bg-green-500/10 border border-green-700/30">
              <p className="text-sm text-green-400">
                Great read! Your coverage recognition accuracy: {accuracy}%
              </p>
            </div>
          )}

          {response === 'wrong' && (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-700/30">
              <p className="text-sm text-amber-400">
                The correct read was {formation.name}. Study the safety alignment.
              </p>
            </div>
          )}

          {/* Next Formation */}
          {response !== null && (
            <button
              onClick={handleNext}
              className="flex items-center gap-2 px-5 py-2.5 bg-forge-500 hover:bg-forge-600 text-dark-950 font-bold rounded-lg transition-colors"
            >
              Next Formation
            </button>
          )}
        </div>
      )}

      {/* Stats tracker */}
      <div className="mt-6 pt-5 border-t border-dark-700">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-dark-400">
            Session: <span className="font-mono text-dark-200">{correct}/{total} correct ({progressPct}%)</span>
          </span>
          <span className="text-sm font-mono text-dark-400">{progressPct}%</span>
        </div>
        <div className="w-full bg-dark-800 rounded-full h-3">
          <div
            className="h-3 rounded-full bg-gradient-to-r from-forge-600 to-forge-400 transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>
    </div>
  );
}

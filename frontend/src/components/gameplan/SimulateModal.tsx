/**
 * AdaptAI "Simulate" modal — asks the backend what to do with a specific
 * play vs a specific opponent tendency / coverage shell.
 */

'use client';

import { useEffect, useState } from 'react';
import { Activity, Loader2, X } from 'lucide-react';
import { adaptPlay, type AdaptResponse } from '@/lib/api/gameplan';
import type { Play } from '@/types/gameplan';

interface SimulateModalProps {
  open: boolean;
  play: Play | null;
  opponentTendency: string;
  opponentArchetype?: string | null;
  titleId: string;
  onClose: () => void;
}

export default function SimulateModal({
  open,
  play,
  opponentTendency,
  opponentArchetype,
  titleId,
  onClose,
}: SimulateModalProps) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AdaptResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !play) return;
    setLoading(true);
    setResult(null);
    setError(null);
    adaptPlay({
      play: { ...play },
      opponentTendency,
      titleId,
      opponentArchetype,
    })
      .then(setResult)
      .catch(() => setError('AdaptAI hit a snag — try again.'))
      .finally(() => setLoading(false));
  }, [open, play, opponentTendency, titleId, opponentArchetype]);

  if (!open || !play) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm px-4">
      <div className="relative w-full max-w-lg rounded-xl border border-forge-500/30 bg-dark-900 shadow-2xl">
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute right-3 top-3 text-dark-500 hover:text-dark-200"
        >
          <X className="h-5 w-5" />
        </button>
        <div className="border-b border-dark-700/50 px-6 py-4">
          <p className="text-xs uppercase tracking-wider text-forge-400">
            <Activity className="mr-1 inline h-3.5 w-3.5" /> AdaptAI · Simulate
          </p>
          <h2 className="mt-1 text-lg font-bold text-dark-50">{play.name}</h2>
          <p className="mt-0.5 text-xs text-dark-400">
            If opponent runs <span className="font-semibold text-dark-200">{opponentTendency}</span>:
          </p>
        </div>
        <div className="px-6 py-5">
          {loading && (
            <p className="flex items-center gap-2 text-sm text-dark-300">
              <Loader2 className="h-4 w-4 animate-spin" />
              Asking AdaptAI for an adjustment…
            </p>
          )}
          {error && <p className="text-sm text-red-400">{error}</p>}
          {result && (
            <div className="space-y-3">
              <div className="rounded-lg border border-forge-500/30 bg-forge-500/5 p-3">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-forge-400">
                  Adjustment
                </p>
                <p className="mt-1 text-sm text-dark-100">{result.adjustment}</p>
                {result.audible_to && (
                  <p className="mt-1 text-xs text-dark-400">
                    Audible to: <span className="font-semibold text-forge-400">{result.audible_to}</span>
                  </p>
                )}
              </div>
              <div className="rounded-lg border border-dark-700/50 bg-dark-800/40 p-3">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-dark-400">
                  Reasoning · confidence {result.confidence}%
                </p>
                <p className="mt-1 text-xs text-dark-200">{result.reasoning}</p>
                <p className="mt-2 text-[10px] text-dark-500">
                  source: {result.source}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

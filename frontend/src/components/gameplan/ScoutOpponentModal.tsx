/**
 * Scout an opponent — populates Opponent.tendencies via Claude (or a
 * deterministic archetype heuristic when no key is set) so subsequent
 * gameplan generations cite real per-opponent data.
 */

'use client';

import { useState } from 'react';
import { Eye, Loader2, X } from 'lucide-react';
import { scoutOpponent, type ScoutResponse } from '@/lib/api/gameplan';

interface ScoutOpponentModalProps {
  open: boolean;
  opponentId: string;
  opponentName: string;
  onClose: () => void;
  onScouted: (res: ScoutResponse) => void;
}

export default function ScoutOpponentModal({
  open,
  opponentId,
  opponentName,
  onClose,
  onScouted,
}: ScoutOpponentModalProps) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScoutResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await scoutOpponent(opponentId);
      setResult(res);
      onScouted(res);
    } catch {
      setError('ScoutBot hit a snag — try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm px-4">
      <div className="relative w-full max-w-md rounded-xl border border-forge-500/30 bg-dark-900 shadow-2xl">
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
            <Eye className="mr-1 inline h-3.5 w-3.5" /> ScoutBot
          </p>
          <h2 className="mt-1 text-lg font-bold text-dark-50">Scout {opponentName}</h2>
          <p className="mt-1 text-xs text-dark-400">
            Builds a tendency dossier (top coverage, blitz rate, behavioral signals)
            and stores it on the opponent so GameplanAI can cite real numbers.
          </p>
        </div>
        <div className="space-y-4 px-6 py-5">
          {error && <p className="text-sm text-red-400">{error}</p>}
          {!result && !loading && (
            <button
              type="button"
              onClick={run}
              className="inline-flex items-center gap-2 rounded-lg bg-forge-500 px-4 py-2 text-sm font-bold text-dark-950 hover:bg-forge-400"
            >
              <Eye className="h-4 w-4" /> Run ScoutBot
            </button>
          )}
          {loading && (
            <p className="flex items-center gap-2 text-sm text-dark-300">
              <Loader2 className="h-4 w-4 animate-spin" />
              Building dossier…
            </p>
          )}
          {result && (
            <div className="space-y-3">
              <p className="text-xs text-dark-400">Dossier ready · source: {result.source}</p>
              <pre className="max-h-72 overflow-auto rounded-lg bg-dark-800 p-3 text-[11px] leading-snug text-dark-200">
                {JSON.stringify(result.tendencies, null, 2)}
              </pre>
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg bg-forge-500 px-4 py-2 text-sm font-bold text-dark-950 hover:bg-forge-400"
              >
                Done
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Post-game flow — three modals chained together:
 *   1. PostGameResultModal  — outcome / score / kill-shot worked / note
 *   2. LoopAIUpdateModal    — what LoopAI learned + next-step CTAs
 *   3. SessionSummaryModal  — final session totals on End Session
 *
 * The dashboard composes these, but the state machine for which modal is
 * open is driven from the sessionStore's gameCount + results + a small
 * `step` prop.
 */

'use client';

import { useState } from 'react';
import { Trophy, X as XIcon, Repeat, Square, Sparkles } from 'lucide-react';
import { clsx } from 'clsx';
import { Modal } from '@/components/shared/Modal';
import {
  useSessionStore,
  sessionDurationSeconds,
  type SessionGameResult,
} from '@/lib/sessionStore';

// ---------------------------------------------------------------------------
// Result modal
// ---------------------------------------------------------------------------

interface PostGameResultModalProps {
  open: boolean;
  opponent: string;
  killShotName: string;
  onClose: () => void;
  onSubmit: (result: SessionGameResult) => void;
}

const OUTCOMES: { value: SessionGameResult['outcome']; label: string; icon: React.ReactNode; tone: string }[] = [
  { value: 'won', label: 'Won', icon: <Trophy className="mr-1.5 inline h-3.5 w-3.5" />, tone: 'border-forge-500 bg-forge-500/15 text-forge-400' },
  { value: 'lost', label: 'Lost', icon: <XIcon className="mr-1.5 inline h-3.5 w-3.5" />, tone: 'border-red-500 bg-red-500/15 text-red-400' },
  { value: 'mixed', label: 'Close game', icon: null, tone: 'border-amber-500 bg-amber-500/15 text-amber-400' },
];

const KILLSHOT_OPTS: { value: SessionGameResult['killShotWorked']; label: string }[] = [
  { value: 'yes', label: 'Yes' },
  { value: 'partly', label: 'Partly' },
  { value: 'no', label: 'No' },
];

export function PostGameResultModal({
  open,
  opponent,
  killShotName,
  onClose,
  onSubmit,
}: PostGameResultModalProps) {
  const [outcome, setOutcome] = useState<SessionGameResult['outcome'] | null>(null);
  const [myScore, setMyScore] = useState('');
  const [theirScore, setTheirScore] = useState('');
  const [killShotWorked, setKillShotWorked] =
    useState<SessionGameResult['killShotWorked'] | null>(null);
  const [note, setNote] = useState('');

  const reset = () => {
    setOutcome(null);
    setMyScore('');
    setTheirScore('');
    setKillShotWorked(null);
    setNote('');
  };

  const handleSubmit = () => {
    if (!outcome || !killShotWorked) return;
    onSubmit({
      outcome,
      myScore: Number(myScore) || 0,
      theirScore: Number(theirScore) || 0,
      killShotWorked,
      note: note.trim(),
      loggedAt: Date.now(),
    });
    reset();
  };

  return (
    <Modal open={open} onClose={onClose} title={`How did it go vs ${opponent}?`} size="md">
      <div className="space-y-5">
        <div>
          <p className="mb-2 text-sm font-medium text-dark-200">Result</p>
          <div className="grid grid-cols-3 gap-2">
            {OUTCOMES.map((o) => (
              <button
                key={o.value}
                type="button"
                onClick={() => setOutcome(o.value)}
                className={clsx(
                  'rounded-lg border px-3 py-2 text-sm font-semibold transition-all',
                  outcome === o.value
                    ? o.tone
                    : 'border-dark-700 bg-dark-800 text-dark-300 hover:border-dark-600'
                )}
              >
                {o.icon}
                {o.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-dark-200">Score</p>
          <div className="flex items-center gap-2">
            <input
              type="number"
              inputMode="numeric"
              value={myScore}
              onChange={(e) => setMyScore(e.target.value)}
              placeholder="Me"
              className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-50 placeholder-dark-500 focus:border-forge-500 focus:outline-none"
            />
            <span className="text-dark-500">—</span>
            <input
              type="number"
              inputMode="numeric"
              value={theirScore}
              onChange={(e) => setTheirScore(e.target.value)}
              placeholder="Them"
              className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-50 placeholder-dark-500 focus:border-forge-500 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-dark-200">
            Did <span className="font-semibold text-forge-300">{killShotName}</span> work?{' '}
            <span className="text-dark-500">(your kill shot)</span>
          </p>
          <div className="grid grid-cols-3 gap-2">
            {KILLSHOT_OPTS.map((k) => (
              <button
                key={k.value}
                type="button"
                onClick={() => setKillShotWorked(k.value)}
                className={clsx(
                  'rounded-lg border px-3 py-2 text-sm font-semibold transition-all',
                  killShotWorked === k.value
                    ? 'border-forge-500 bg-forge-500/15 text-forge-400'
                    : 'border-dark-700 bg-dark-800 text-dark-300 hover:border-dark-600'
                )}
              >
                {k.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-dark-200">
            Quick note <span className="text-dark-500">(optional)</span>
          </p>
          <input
            type="text"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="What stood out?"
            className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-50 placeholder-dark-500 focus:border-forge-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center justify-end border-t border-dark-700/50 pt-4">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!outcome || !killShotWorked}
            className="rounded-lg bg-forge-500 px-4 py-2 text-sm font-semibold text-dark-950 transition-colors hover:bg-forge-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Submit
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// LoopAI update modal
// ---------------------------------------------------------------------------

interface LoopAIUpdateModalProps {
  open: boolean;
  killShotName: string;
  result: SessionGameResult | null;
  onClose: () => void;
  onPlayAnother: () => void;
  onEndSession: () => void;
}

export function LoopAIUpdateModal({
  open,
  killShotName,
  result,
  onClose,
  onPlayAnother,
  onEndSession,
}: LoopAIUpdateModalProps) {
  const summary = result
    ? result.killShotWorked === 'yes'
      ? `${killShotName} confidence raised after a successful execution. Coverage Read Speed: +2 points.`
      : result.killShotWorked === 'partly'
      ? `${killShotName} held steady — partial execution logged for next adjustment.`
      : `${killShotName} confidence dropped — alternative options will be surfaced next session.`
    : 'PlayerTwin updated with this game\'s data.';

  return (
    <Modal open={open} onClose={onClose} title="LoopAI Updated" size="md">
      <div className="space-y-5">
        <div className="flex items-start gap-3 rounded-lg border border-forge-500/30 bg-forge-500/10 p-4">
          <Sparkles className="h-5 w-5 flex-shrink-0 text-forge-400" />
          <p className="text-sm leading-relaxed text-dark-100">"{summary}"</p>
        </div>

        <div className="flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={onEndSession}
            className="inline-flex items-center gap-1.5 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm font-semibold text-red-300 transition-colors hover:bg-red-500/20"
          >
            <Square className="h-3.5 w-3.5" />
            End Session
          </button>
          <button
            type="button"
            onClick={onPlayAnother}
            className="inline-flex items-center gap-1.5 rounded-lg bg-forge-500 px-4 py-2 text-sm font-bold text-dark-950 transition-colors hover:bg-forge-400"
          >
            <Repeat className="h-3.5 w-3.5" />
            Play Another Game
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Session summary modal
// ---------------------------------------------------------------------------

interface SessionSummaryModalProps {
  open: boolean;
  onClose: () => void;
}

export function SessionSummaryModal({ open, onClose }: SessionSummaryModalProps) {
  const session = useSessionStore((s) => s.session);
  const endSession = useSessionStore((s) => s.endSession);

  if (!session) return null;

  const wins = session.results.filter((r) => r.outcome === 'won').length;
  const losses = session.results.filter((r) => r.outcome === 'lost').length;
  const totalSeconds = sessionDurationSeconds(session);
  const minutes = Math.floor(totalSeconds / 60);

  // Most-used kill shot — when we don't have detailed play data, fall back
  // to the drill name or a generic "Top Play".
  const successCount = session.results.filter((r) => r.killShotWorked === 'yes').length;
  const topPlay = session.drillId ?? 'Top Play';

  const handleClose = () => {
    endSession();
    onClose();
  };

  return (
    <Modal open={open} onClose={handleClose} title="Session Summary" size="md">
      <div className="space-y-4">
        <SummaryRow label="Games played" value={String(session.gameCount)} />
        <SummaryRow label="Record" value={`${wins}-${losses}`} />
        <SummaryRow
          label="Best play"
          value={`${topPlay} (worked in ${successCount} of ${session.gameCount})`}
        />
        <SummaryRow label="Session duration" value={`${minutes} min`} />
        <SummaryRow
          label="LoopAI"
          value={`${session.results.length} ${session.results.length === 1 ? 'thing' : 'things'} learned`}
        />
        <SummaryRow
          label="TiltGuard"
          value={
            successCount >= session.gameCount && session.gameCount > 0
              ? 'Performance improved'
              : session.gameCount > 0
              ? 'Performance stable'
              : 'No games logged'
          }
        />

        <div className="flex justify-end border-t border-dark-700/50 pt-4">
          <button
            type="button"
            onClick={handleClose}
            className="rounded-lg bg-forge-500 px-4 py-2 text-sm font-semibold text-dark-950 transition-colors hover:bg-forge-400"
          >
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-dark-700/40 pb-2 text-sm">
      <span className="text-dark-400">{label}</span>
      <span className="font-semibold text-dark-100">{value}</span>
    </div>
  );
}

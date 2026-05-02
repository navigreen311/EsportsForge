/**
 * Session-end review modal — 3 quick questions before closing a session.
 */

'use client';

import { useState } from 'react';
import { clsx } from 'clsx';
import { Modal } from '@/components/shared/Modal';

export type SessionOutcome = 'won' | 'lost' | 'mixed';
export type RecAdherence = 'yes' | 'partly' | 'no';

export interface SessionReviewPayload {
  outcome: SessionOutcome;
  adherence: RecAdherence;
  note: string;
}

interface SessionReviewModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (payload: SessionReviewPayload) => void;
  onSkip: () => void;
}

const OUTCOMES: { value: SessionOutcome; label: string; tone: string }[] = [
  { value: 'won', label: 'Won', tone: 'border-forge-500 bg-forge-500/15 text-forge-400' },
  { value: 'lost', label: 'Lost', tone: 'border-red-500 bg-red-500/15 text-red-400' },
  { value: 'mixed', label: 'Mixed', tone: 'border-amber-500 bg-amber-500/15 text-amber-400' },
];

const ADHERENCE: { value: RecAdherence; label: string }[] = [
  { value: 'yes', label: 'Yes' },
  { value: 'partly', label: 'Partly' },
  { value: 'no', label: 'No' },
];

export function SessionReviewModal({
  open,
  onClose,
  onSubmit,
  onSkip,
}: SessionReviewModalProps) {
  const [outcome, setOutcome] = useState<SessionOutcome | null>(null);
  const [adherence, setAdherence] = useState<RecAdherence | null>(null);
  const [note, setNote] = useState('');

  const reset = () => {
    setOutcome(null);
    setAdherence(null);
    setNote('');
  };

  const handleSubmit = () => {
    if (!outcome || !adherence) return;
    onSubmit({ outcome, adherence, note: note.trim() });
    reset();
  };

  const handleSkip = () => {
    reset();
    onSkip();
  };

  return (
    <Modal open={open} onClose={onClose} title="Session Review" size="md">
      <div className="space-y-5">
        <div>
          <p className="mb-2 text-sm font-medium text-dark-200">How did it go?</p>
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
                {o.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-dark-200">
            Did you follow the recommendation?
          </p>
          <div className="grid grid-cols-3 gap-2">
            {ADHERENCE.map((a) => (
              <button
                key={a.value}
                type="button"
                onClick={() => setAdherence(a.value)}
                className={clsx(
                  'rounded-lg border px-3 py-2 text-sm font-semibold transition-all',
                  adherence === a.value
                    ? 'border-forge-500 bg-forge-500/15 text-forge-400'
                    : 'border-dark-700 bg-dark-800 text-dark-300 hover:border-dark-600'
                )}
              >
                {a.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-dark-200">
            One quick note <span className="text-dark-500">(optional)</span>
          </p>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={3}
            placeholder="What stood out?"
            className="w-full resize-none rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-50 placeholder-dark-500 focus:border-forge-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center justify-between border-t border-dark-700/50 pt-4">
          <button
            type="button"
            onClick={handleSkip}
            className="rounded-lg px-4 py-2 text-sm font-medium text-dark-400 transition-colors hover:bg-dark-800 hover:text-dark-200"
          >
            Skip
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!outcome || !adherence}
            className="rounded-lg bg-forge-500 px-4 py-2 text-sm font-semibold text-dark-950 transition-colors hover:bg-forge-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Submit
          </button>
        </div>
      </div>
    </Modal>
  );
}
